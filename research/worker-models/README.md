# Per-commission model and effort requests

Source capability for a8005, 21 October 2026. Takes effect after source landing;
no live house restart, account change or delegation was performed by this worker.

## For residents

Set the request on the commission **before asking it**:

```text
do prop <commission> requested_model=claude-sonnet-5 requested_effort=low commission=asked
```

That is a concrete metadata-supported example, not a recommendation for every
job. Choose enough capability for the task. Omit both requests to retain current
selection. Effort alone applies to the normally selected model, and still requires
that model to advertise that effort.

Use exact runtime catalog identifiers, not `auto`, `haiku`, `sonnet` or other
moving aliases. A model is not made available just by naming it. Claude checks
sign-in and the CLI's initialization catalog without sending a model prompt.
Codex requires its existing reviewed pin/catalog, a ChatGPT subscription identity,
and the running CLI's model and effort capabilities before creating/resuming a
thread or starting inference. Missing metadata, unavailable models, unsupported
effort and `ultra` are refused, with no fallback. `ultra` can entail delegation,
which this feature does not admit.

The card gets `selection_status`, `selection_error`, `resolved_model`,
`resolved_effort`, `actual_model` and `actual_effort`. Resolved means selected
configuration, **not** proof a model ran. Actual fields come only from runtime
events; empty means unreported. A reported mismatch refuses output/future turns.
No inferred effort, price or savings is presented as a receipt.

An unchanged refusal does not repeatedly probe or comment. Correct the requested
fields. If metadata was temporarily unavailable and the same request should be
retried, change `requested_retry` to a fresh token (for example `retry-2`).
This permits another validation attempt, not a bypass of validation.

Requests never rewrite a saved conversation's provider/model/known effort.
A changed request that conflicts with saved context is refused and leaves that
context and unheard/pending lines intact. An old session with unknown effort
cannot satisfy a new explicit effort request. Use a new commission for a different
runtime; `worker_fresh=yes` does not erase an existing card's context.

Fresh explicit requests use disposable per-card context rather than adopting a
standing builder's possibly incompatible conversation. They use the existing
shared priority admission and count toward the same total four. Requests constrain
runtime eligibility without adding provider queues/reserved slots. Existing
unrequested jobs retain their selection behavior. Quota fallback cannot silently
switch an explicitly requested card to another provider.

Legacy `worker_model`/`worker_provider` are selected-runtime labels that a mixed
pool can overwrite; do not use them as the new request interface.
`worker_reasoning` remains a legacy Codex effort input; Claude's
`worker_claude_effort` remains the default. The new request changes neither global
setting. Residents themselves and Alex's direct app sessions are outside this
per-commission interface.

## Receipts and limits

Per-worker durable state stores the request, resolved selection and actual/usage
receipts under `selection`. The local worker transcript adds `selection` and
`runtime_receipt` records. Usage keeps only numeric token/cache/cost metadata
reported by the runtime, with original field names. Claude's result can report
`usage`, `modelUsage`, `total_cost_usd`; Codex can report `tokenUsage` without
currency cost or actual effort. These are runtime receipts, not plan-quota
percentages or a normalized cross-provider bill. Current-run state resets on a
new process; earlier receipts remain in the durable transcript.

No new delegated process, spawning policy, subtask authority or recursive agent
support is implemented. Existing tool/pin/account boundaries remain in force.

## Evidence

**Ran:** Claude CLI **2.1.287**, metadata-only, 21 October 2026. CLI auth reported
logged in; a control `initialize` returned exact identifiers including
`claude-sonnet-5`, `claude-opus-5`, `claude-fable-5`,
`claude-opus-4-8`, `claude-opus-4-7`, `claude-opus-4-6` and
`claude-sonnet-4-6`. Sonnet 5 advertised low, medium, high, xhigh and max.
Haiku appeared only as an alias with no effort metadata, so this interface cannot
select it confidently. This is a dated observation, not a hardcoded allowlist or
proof that an inference request will be accepted despite quota/provider outages.
No user message, paid inference or saved conversation was sent by this probe.

**Read:** the existing reviewed Codex catalog metadata covers Astra and Sol;
no smaller Codex model was added or claimed available. Each requested start still
checks authenticated runtime capabilities. No real Codex metadata probe or model
turn was run for this commission.

**Ran:** `test_worker_selection.py` uses mocked CLI/processes and an in-memory
world; it covers exact requests, malformed/unavailable capabilities, efforts,
four-slot admission, refusal correction/retry/no polling, saved-context fencing,
pending text, actual/unknown receipts and explicit quota preservation.
`test_worker_pool.py` and `test_builders.py` check existing admission and
standing-builder compatibility. These are logic/transport tests, not paid-model
quality, latency, token savings or production activation evidence.

Primary sources read for the existing CLI control protocol and effort types:

- [Agent SDK control initialization](https://github.com/anthropics/claude-agent-sdk-python/blob/main/src/claude_agent_sdk/_internal/query.py)
- [Agent SDK client/server metadata](https://github.com/anthropics/claude-agent-sdk-python/blob/main/src/claude_agent_sdk/client.py)
- [Agent SDK effort types](https://github.com/anthropics/claude-agent-sdk-python/blob/main/src/claude_agent_sdk/types.py)
