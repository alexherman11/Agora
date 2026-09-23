# Astra harness validation — September 5, 2026

## OAuth follow-up: verified live

Final suite with the actual runtime test enabled: **130 passed** (one upstream
Starlette/AnyIO deprecation warning). Ruff check, formatting check and diff
whitespace check passed.

Alex clarified that the connection must use his OpenAI account. The implemented
`openai-account` provider uses the official Codex Python SDK, with managed
ChatGPT OAuth and the existing account sign-in. No API key or extracted OAuth
token was used. The SDK-bundled runtime 0.147.0 rejected Astra with an
upgrade-required error. Explicit runtime 0.153.4 listed and successfully ran
`gpt-6-astra`.

Live checks on September 5:

- Astra created and placed a note in a disposable world through `mint` and
  `place`, attributed to JEFF.
- Astra authored a counter component from scratch, tested it on disposable state,
  activated source revision 1, discovered the action and invoked increment(2).
  Final state was 2, and the rebuilt store equaled the live store. The 62-second
  trial included two self-corrected refusals: reading an absent display facet
  and submitting an incorrectly shaped test case. No human correction was given.
  Full evidence: `astra-oauth-live-counter-2026-09-05.json`.
- Both local servers (8787 and 8788) returned signed-in OpenAI-account status and
  model `gpt-6-astra`. Browser inspection confirmed **Astra · OpenAI account** on
  the existing demo. Its active component remained revision 8; the live authorship
  trial did not replace it. The user's unsent chat draft was preserved on reload.

The actual Codex runtime was also tested against a local mock inference server.
The test executes code in the real tool-composition host to enumerate its tools
and globals. The resulting inventory is the Agora registry plus Astra's UTC
clock. Process, fetch, require, shell execution and apply_patch are unavailable.
An initial inventory exposed orchestrator skills; the final configuration disables
orchestrator skills/MCP and host skill discovery. The mock receives no account
Authorization header. This test avoids model spending while testing the real
runtime, rather than accepting a model's claim about its capabilities.

The account adapter preserves the single verb write path. Codex owns its inner
loop; Agora owns tools, dispatch, cancellation and turn budgets. This differs from
the earlier API-key Agents SDK design below. The visible login button and account
lifecycle have mocked protocol coverage; a fresh interactive OAuth grant was not
performed because the account was already signed in. Token refresh remains
Codex-managed and was not forced for the test. These successful small tasks are
not a comprehensive assessment of Astra's reliability or complex authorship.

Runtime configuration is audited against the official pinned source:
[tool registration](https://github.com/openai/codex/blob/rust-v0.153.4/codex-rs/core/src/tools/spec_plan.rs),
[environment contract](https://github.com/openai/codex/blob/rust-v0.153.4/codex-rs/app-server-protocol/src/protocol/v2/thread.rs),
and [skill-tool gating](https://github.com/openai/codex/blob/rust-v0.153.4/codex-rs/ext/skills/src/tools/mod.rs).
Re-run the inventory test when changing the runtime or configuration.

## Earlier API-key adapter validation (historical)

Evidence for [[Astra Harness]]. Alex selected the OpenAI Agents SDK route,
retaining Agora's tools and outer loop.

## Implemented

- Provider selection in `jeff/agent.py`; existing Anthropic configurations remain
  compatible. The selected OpenAI model is `gpt-6-astra`.
- `jeff/openai_agent.py` runs the actual Agents SDK for one model/tool step,
  then refreshes world context and derived actions in Agora's finite outer loop.
- Only registry/manifest-derived function tools; callbacks retain actor attribution,
  kernel validation, the dispatch lock, and Stop behavior.
- SDK-preserved reasoning and call/output history, without accumulating old world
  projections. Missing credentials refuse before history or world mutation.
- Responses transport, medium reasoning, 32768 output-token ceiling, no sampling
  settings, no hosted tools, no tracing, no retries, and a 120-second timeout.

## Checks

`uv run pytest`: **122 passed**, one upstream Starlette/AnyIO deprecation warning.
`uv run ruff check .`, `uv run ruff format --check .`, and `git diff --check` passed.

Eight SDK-specific tests execute the actual SDK runner with inference replaced:

1. World-tool dispatch, attribution, replay equality, refreshed perception, and
   retained opaque reasoning/history across steps and user turns.
2. An action appears and executes in the same turn after component activation.
3. Invalid facets and forged actors are returned as refusals without writes.
4. Stop preserves completed writes, refuses later dispatch, and permits a new turn.
5. The outer step budget stops while retaining completed tool-call/output history.
6. Missing API credentials fail before history or world changes.
7. An unknown tool is an error result the model can correct, not a hidden capability.
8. The actual OpenAI Responses client serializes requests through an HTTP stub:
   `/v1/responses`, Astra model ID, reasoning/settings, derived component schemas,
   `strict=False`, and correlated function outputs on continuation.

The HTTP test uses a dummy credential and `httpx.MockTransport`; it sends no
network traffic. The other tests use SDK `ModelResponse` objects and the real tool
executor. None is a live model result or an account access check.

## Remaining live validation

No `OPENAI_API_KEY` was configured in the Agora environment when checked. The
running personal app and Sonnet demonstration were not switched to an unverified
backend. A key must be configured locally before live Astra use.

After configuration, select `AGORA_JEFF_PROVIDER=openai-agents` and
`AGORA_JEFF_MODEL=gpt-6-astra`, restart, and repeat the disposable-world authored
dragging, second behavior/state/action, and action invocation trial. Preserve all
errors and compare with [[executable-component-validation-2026-09-05]]. Actual
model availability, authoring quality, latency, and cost remain unverified.
