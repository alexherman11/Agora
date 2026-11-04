# Smart search citation audit, second round

2 November 2026. **Read:** public sources fetched through the research browser, with supporting passages inspected. Link reachability is not empirical reproduction. No credentials, account content or private search terms used. Original claims remain bounded to the cited sources' studied systems.

| Original citation | Check and supported claim | Limit |
|---|---|---|
| [BEIR](https://arxiv.org/abs/2104.08663) | Abstract explicitly calls BM25 robust and notes average reranking/late-interaction gains with computational cost. | Does not validate this desktop, chosen Qwen models or personal queries. |
| [RRF](https://cormack.uwaterloo.ca/cormacksigir09-rrf) | Two-page paper fetched; section 1 gives reciprocal rank sum and fixed pilot constant 60; abstract identifies TREC/LETOR experiments. | Fusion gains are empirical for those experiments, not guaranteed here. |
| [BERT reranking](https://arxiv.org/abs/1901.04085) | Abstract fetched; [full HTML method](https://arxiv.org/html/1901.04085v5), section 2, feeds query and passage jointly and scores candidates. | Training/benchmarks are not available local model evidence. |
| [RAG](https://arxiv.org/abs/2005.11401) | Abstract describes parametric generation plus dense Wikipedia retrieval. | Motivation for grounding, not a guarantee of correctness or citation completeness. |
| [Lost in the Middle](https://arxiv.org/abs/2307.03172) | Abstract reports positional degradation on its evaluated QA/key-value tasks. | Not a measured claim about installed Qwen models. |
| [Indirect prompt injection](https://arxiv.org/abs/2302.12173) | Abstract explicitly identifies injection through retrieved content and demonstrations against real/synthetic applications. | Does not certify our proposed defenses. |
| [M3 embeddings](https://arxiv.org/abs/2402.03216) | Abstract specifies multilingual dense/sparse/multi-vector support. | Model not present in observed Ollama inventory; no acquisition/quality test. |
| [FTS5](https://sqlite.org/fts5.html) | Sections 4.3.4 and 5.1 support trigram substring matching, BM25 weighting and snippets. | Not general edit-distance typo correction; local runtime extension availability not tested. |
| [Gmail scopes](https://developers.google.com/workspace/gmail/api/auth/scopes) | Scope table states metadata excludes bodies and distinguishes readonly; restricted-scope table inspected. | OAuth approval and compliance obligations for any actual deployment remain to assess. |
| [Gmail messages.list](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/list) | `q` parameter explicitly unavailable with `gmail.metadata`; listing returns identifiers, with details fetched separately. | Metadata-only consent cannot be advertised as provider full-text search. |
| [Gmail sync](https://developers.google.com/workspace/gmail/api/guides/sync) | Limitations state out-of-range history yields HTTP 404 requiring full sync. | No real mailbox/cursor checked. |
| [Graph permissions](https://learn.microsoft.com/en-us/graph/permissions-reference) | **Not reverified this round:** browser fetch timed out. Successfully read in round one. | Retain earlier evidence label; do not describe this link as freshly verified. Basic/body distinctions need recheck before connector implementation. |
| [Graph delta](https://learn.microsoft.com/en-us/graph/api/message-delta?view=graph-rest-1.0) | Body text fetched despite a generic sign-in banner: folder added/deleted/updated changes, state tokens, least-privilege table. | Delta is change tracking; page also explicitly says no `$search` support. Not a general semantic query endpoint. |
| [Windows Search](https://learn.microsoft.com/en-us/windows/win32/search/-search-3x-wds-overview) | Service section describes indexed catalogue/properties/content and scopes. | Historical Win32 overview, not verification of this computer's Windows version, service or coverage. |

Original link audit: **13 successful fetches, 1 timeout**. “Verified” here means the specific textual claim and reachable page, not a full paper replication or guarantee of current deployment compatibility.

Additional primary API documentation checked for the addendum:

- [Ollama tags](https://docs.ollama.com/api/tags) and [running models](https://docs.ollama.com/api/ps): document the GET metadata endpoints used. Actual loopback responses were read; installed is not loaded.
- [Generate](https://docs.ollama.com/api/generate) and [structured outputs](https://docs.ollama.com/capabilities/structured-outputs): document schema formats. Installed runtime support and semantic reliability **not tested**.
- [Embed](https://docs.ollama.com/api/embed): documents a separate embedding operation. Its existence does not prove either installed generative model supports suitable embeddings. No embed request ran.

All performance, model-quality and evaluation thresholds in the addendum are **imagined targets**. The new local model inventory is a **ran metadata observation**; the October proof remains **read historical evidence**, not tests run in this task.
