# One search, with local understanding from the first slice

Second research/design round for JEFF, 2 November 2026. **No implementation authorized or performed.**

**Recommendation — imagined:** one “Search everything” entry should interpret the request locally, retrieve across all enabled eligible sources, and present evidence-backed tools, files, messages, answers and public alternatives together. The first prototype must demonstrate model-based understanding of unfamiliar phrasing and combined constraints. The catalogue supplies grounded facts and deterministic actions; it is not the intelligence or the destination.

This revises the first note's catalogue-only first phase and separate web-search button as the normal experience. The earlier inventory, opt-in boundaries and permission requirements still apply. All layouts and proposed behavior below are **imagined**; **ran** denotes metadata/document checks only, and **read** denotes source/document inspection. No inference, connector activation, account access or behavioral/performance testing occurred.

## One entry and clear coverage

**Imagined defaults for review:** a compact launcher search entry opens a dedicated light search surface. Pressing Enter submits the request, never executes it as a world command. Optional filters narrow an existing search; ordinary queries require no source selection. Results arrive progressively with stable selection, source badges and a compact coverage row:

```text
Search everything: photo editor
World · checked   Apps · known entries only
Files · not connected   Email · not connected   Web · not enabled

BEST WAYS TO DO THIS
Fixture Local Editor   [On this computer]   [Open]
Fixture Browser Editor [Web alternative]   [Visit official site]
More tools | Related discussions | Files
```

The Web card above exists only when that source is enabled and returns evidence. Otherwise its position says “Web alternatives unavailable — provider not enabled”; it must not contain model-invented recommendations. Known app pins, uploaded documents and world chats remain distinct source capabilities. “All” means all enabled eligible sources, not complete access to the computer.

After one explicit provider/egress opt-in, public web discovery runs in parallel for ordinary public requests such as “photo editor,” “free offline image editor,” or “how do I crop a circle?” Installed/native tools and public alternatives share the main result area, labelled accurately; neither a web click nor a search result installs anything. Relevant web answers need linked sources and checked dates. Local apps may rank above otherwise equal web options because they are available now, but a missing required capability disqualifies them.

### Public requests versus personal ones

**Imagined:** egress is decided before source retrieval. The local model may suggest a public intent; it cannot authorize transmission.

| Request class | Default routing after web opt-in |
|---|---|
| Clearly generic public topic/task | Fan out automatically to local sources and public web. Send only the public query typed for this request. |
| Personal/contextual: “my,” “we decided,” “last week's download,” people, paths, selected content, account data | Local/approved private sources only. Show “Web held: personal context”; offer an optional editable public reformulation. |
| Unfamiliar entity, ambiguous referent, mixed public/private request, uncertain classifier | Keep local; one “Search a public version” choice if useful. Do not silently sanitize by dropping words. |
| Explicit “on the web” with personal material | Show the exact proposed external query for one-click confirmation; explicit web intent alone does not override private-data boundaries. |

A bounded host gate admits a deliberately conservative set of general public task constructions/terms, rejects private/context markers and unknown entities, and requires the local classifier not to veto. It consumes only current input and explicit mode, never private search results, chat memory or clipboard content. A positive classification outside that public policy stays local. This gate is a privacy mechanism, not the semantic retrieval vocabulary. It can be expanded through reviewed public examples without adding aliases for every result.

No automatic gate can prove that an apparently ordinary word is not a secret codename. Explain the web mode once, keep its indicator visible and provide a persistent local-only toggle. Never call such a heuristic a guarantee of query confidentiality. If Alex needs every raw query confidential, local-only must be the default and automatic public fan-out is incompatible with that preference. Proposed default is automatic web only for the bounded generic class after opt-in; uncertain cases remain private. No such opt-in or mode change happens in this research.

“Remove a background without uploading” may search public software documentation without sending any image. It constrains where the **photo** is processed; it does not automatically prohibit fetching public documentation. An explicit “no network at all” additionally disables web retrieval. Display this distinction in the interpretation, rather than silently treating offline, no upload and browser-based as synonyms.

## Local routes that are actually plausible

**Ran, read-only:** pinned Python requested only loopback `GET /api/tags`, `/api/ps` and `/api/version`, with proxies disabled. Installed metadata reported Qwen 3.5 9B, **6,550,825,550 bytes**, and Qwen 2.5 3B, **1,929,912,432 bytes**, both Q4_K_M. Running-model list was **empty**; service version reported **0.40.10**. World `rows model-settings` selected `qwen3.5:9b`. These are momentary metadata observations, not inference quality, memory consumption or cold-start timings.

| Route | Read evidence | Design assessment, unmeasured |
|---|---|---|
| Existing selected Qwen 3.5 9B via Agora's local-model process | Installed and selected; fixed loopback generate client in `modules/model/model.py`. | First candidate for a bounded intent/constraint and relevance pass. No settings switch needed; larger model may impose unacceptable cold latency/resource use. |
| Installed Qwen 2.5 3B through that same broker | Installed now; older proof documents previous use, not current search quality. | Smaller alternative to compare later on exactly the same hidden cases. Do not change the live selection to compare it. A fixture broker could explicitly select it after review. |
| Dedicated local embedding/cross-encoder | No dedicated encoder appears in the observed Ollama model list. | Strong scalable alternative once approved weights/runtime exist. Not an already established day-one route. An `embedding_length` metadata field does not establish supported or useful search embeddings. |
| Direct Python ONNX/Transformers/llama.cpp runtime | Distribution metadata for `onnxruntime`, `torch`, `transformers`, `sentence-transformers`, `llama-cpp-python` and `ollama` was absent in the pinned environment. | No evidence this route is ready here. This is not a full-machine software audit. The HTTP broker needs no Python Ollama package. |

**Read:** current model words support ask, summarize, classify and status, not a typed search-plan/reranking operation. The client uses bounded context, a shared inference lock and budgets; classify writes a label. It must not be repurposed to write transient search interpretations into source items. Even status charges its attempt counter, so this round used metadata GETs rather than that word.

**Read:** Ollama documents [JSON/schema output](https://docs.ollama.com/api/generate) and [structured outputs](https://docs.ollama.com/capabilities/structured-outputs). A proposed bounded read operation in the existing local process would need reviewed source work, strict output validation and a suitable search budget. Runtime schema compatibility was **not tested**. Valid JSON does not imply correct intent. Do not bypass the broker's privacy, grants, quota or concurrency controls by adding another inference client.

## Understanding beyond aliases on day one

**Imagined vertical pipeline:** local interpretation plus bounded semantic relevance over permitted records, alongside exact lexical matching. For a tiny corpus, score all authorized short descriptors in one model pass; do not require a matching keyword to admit a candidate. This avoids the false demonstration where a model only reranks results an alias table has already found. At scale, replace this linear semantic scan with measured local hybrid retrieval; retain the same source and action contract.

The model returns a schema with candidate intents, semantic query expressions, requested constraints with input spans, candidate relevance and supporting evidence spans. It cannot return executable actions, paths, provider calls or permission decisions. Host code accepts only existing candidate identifiers, validates evidence spans against the permitted supplied text and translates validated constraints to typed predicates. A span's presence verifies provenance, not entailment; uncertain semantic conclusions remain labelled, and “selected/decided” answers need actual decision evidence.

Query-time semantics and source facts have different roles. The model can interpret “cut the person out, keep the picture here” as likely background removal with local processing. It cannot declare an app's processing local. A hard no-upload requirement is satisfied only by reviewed/current source facts `processing=local`; unknowns stay in an “unverified” group and are excluded from the recommended action set. Read-only web search cannot certify an app's actual runtime network behavior.

| Query | Semantic work | Deterministic checks and result |
|---|---|---|
| “remove a background without uploading” / unseen “cut the subject free but keep the pixels here” | Infer image segmentation/tool discovery and a no-photo-egress constraint. | Filter supported operation plus evidenced local processing. Offer matching local tools and verified public alternatives; unknown processing is not a match. |
| “open last week's downloaded editor” | Infer a retrieved artifact and launch/open intent, not general tool discovery. | Resolve last full calendar week in America/Los_Angeles, show dates; filter actual download timestamp, not modification time. Installer gets Show in folder; app gets Open only if independently registered/validated. Missing download metadata means unknown, not fabricated history. |
| “find the discussion deciding which editor” / unseen “where did we finally settle the image-tool choice?” | Retrieve decision-bearing discussion despite no shared editor name; distinguish proposal, rejection and final choice. | Return readable message anchors, author/date and context. Conflicting/no explicit decision yields cited discussion candidates, not a claimed agreement. |

User hard constraints remain visible; when the parser cannot reliably resolve one, do not recommend a possibly violating action. A tiny corpus can be scanned semantically, but that does not solve million-item retrieval. Query rewriting helps lexical recall; dense indexing requires a suitable approved encoder. Both are follow-on alternatives evaluated against the same held-out composition cases.

### Example layouts

All names/content below are synthetic fixtures; controls are proposed.

```text
cut the subject free but keep the pixels here
Understood: background removal · photo stays local [Change]
Coverage: Apps known · World current · Web current · Files/Mail unconnected
Fixture Cutout — local processing evidence reviewed · [Open]
Fixture Offline Tool — public alternative, not installed · [Official site]
Unknown processing (2) [Show]       No photo sent anywhere
```

```text
open last week's downloaded editor
Understood: downloads · Oct 26–Nov 1, 2026 · Web held: personal
FixtureEditorSetup.exe — downloaded Oct 29 · Installer · [Show in folder]
Fixture Editor Portable — downloaded Oct 30
  Launch target not verified · [Show in folder]
Coverage: Downloads not connected on the real desktop; fixture example only
```

```text
find the discussion deciding which editor
World: discussion matches · Web held: personal · Mail not connected
Image-tool discussion — Nov 1 · [Open discussion at decision]
  Proposed A → rejected upload requirement → explicit selection of B
  [Decision message] [Earlier proposal]
No explicit decision? Show “Found discussion, could not establish a choice.”
```

## The smallest honest end-to-end slice

**Imagined, after research review:** one hidden fixture surface, the existing local-model process with a reviewed read-only semantic operation, exact lexical baseline, and **36 small records**: 6 tools, 6 download records, 12 discussion messages and 12 public documentation passages. Keep permitted descriptors within the broker's context bound; no private real content. Use unrelated fixture names, descriptive prose and real constraint metadata, not query aliases.

One bounded model pass interprets and ranks the permitted descriptors; host code checks constraints, source scope and evidence, then renders validated actions. Exact lookup renders first. Public and private provider interfaces are both present in the slice: public fan-out is exercised through a **labelled recorded public-provider fixture**, not a claimed live web integration. Unavailable sources have explicit coverage states. Fixture actions target hidden fixture handlers, never Alex's apps.

This is end-to-end from language input through routing, semantic candidate discovery, constraint checking, evidence and action validation. It is **not** an end-to-end live internet/mail/Windows deployment. A separately authorized generic live web-provider contract check is needed before claiming live discovery. Under current boundaries, no connection can be activated to remove that limitation.

The slice must handle all three query families above with held-out paraphrases and counterexamples. Catalogue-plus-aliases alone does not pass. Output grammar, aliases or mocked model answers can test plumbing but cannot constitute evidence of understanding. No generative answer paragraph is necessary: finding the right tool/artifact/decision with the right constraint is sufficient.

Alternatives: (A) catalogue/lexical only is the baseline and outage fallback; (B) **recommended first experiment** is the existing 9B local interpreter plus semantic scan; (C) installed 3B is a competing local experiment if 9B latency fails; (D) dedicated encoder plus lexical fusion and optional local reranking is the scaling candidate, contingent on separately approved availability. External models are excluded for private queries/content.

## Evaluation that can reject this recommendation

**Imagined, not run:** freeze prompts, schema, corpus and baseline before JEFF independently writes a blind set. Use **120 held-out queries**, 20 each for unfamiliar paraphrases, minimal constraint pairs/negation, artifact/time reference, decision/conflict retrieval, public/private ambiguity, and multilingual/typo requests. Add **40 state/attack cases** covering revocation during inference/click, stale indexes, fake capability claims, prompt injection, provider failures and resource pressure. No tuning on blind failures; the next revision gets a fresh set.

Use random fixture names and withhold whole capability compositions from development. Include impossible requests and relevant records with zero important query-word overlap. Pair “without uploading” with “upload is fine”; “downloaded last week” with “modified last week”; “we considered A” with “we chose A”; ordinary public requests with person/path/codename-bearing counterparts. Distractors should deliberately repeat query words while violating the constraint. Swap record order and names to expose positional/name memorization.

Compare lexical+catalogue, 9B semantic scan, 3B semantic scan, and later approved hybrid retrieval on identical candidates and authority snapshots. Measure joint task success@3 **only when intent, constraints, evidence and action are all correct**; also semantic recall over zero-overlap targets, unsupported decisions, inappropriate abstention, and public-route recall/precision. Evaluate full candidate discovery, not reranking with the gold target preinserted.

**Proposed rejection gates:** any observed private sentinel egress, revoked content exposure or unauthorized action rejects the design. Any recommended action violating an explicit hard constraint also blocks release. To justify semantic complexity, require at least a 15 percentage-point improvement over catalogue/lexical on unfamiliar/compositional task success, at least 80% success on that slice, and no more than a 2-point exact-target regression. Require at least 90% automatic web routing on the defined generic-public set without private cases being sent. Treat near-threshold results as inconclusive; report counts, paired differences and uncertainty.

Measure first lexical cards separately (target warm p95 ≤250 ms), semantic completion (target warm p95 ≤2 s) and cold end-to-end completion (target p95 ≤5 s), with no background model preloading hidden from the measurement. These targets are unverified and may reject 9B on this machine. Busy model/provider must preserve usable lexical cards; no cloud fallback. Failed 9B latency favors the 3B competitor or a later encoder, not a claim that aliases satisfy the task.

## Verified claims and remaining choices

**Read/ran:** the [citation audit](smart-search-citation-audit-2026-11-02.md) rechecked the first note's 14 external links and key support passages: 13 fetched successfully in this round; Graph's permissions-reference fetch timed out and is explicitly not reverified. Research abstracts support architectural motivation, not local performance claims. No paper benchmark was reproduced.

**Defaults for review:** one blended entry, explicit coverage, bounded automatic public fan-out after one provider opt-in, private/ambiguous queries local, existing selected 9B as first semantic experiment, deterministic authority/constraints/actions, and no free-form answer until evidence works. Unresolved: cold latency, schema support in the installed runtime, whether 3B handles the compositions, a suitable encoder for scale, provider selection/terms/budget, and connector consent/retention. JEFF can review these defaults without asking Alex to pre-specify every source or capability.
