# Astra Harness

**Adapter-lineage record — September 5, 2026; imported September 10.** The older
`docs` prototype and Agora3 both use the official Codex SDK, managed ChatGPT sign-in,
Astra and an intentionally narrow Agora tool surface, but their modules, operation
registries and loop limits differ. This document preserves the earlier adapter's
exact reasoning and evidence; unqualified module paths and limits below refer to
that prototype. For the current `src/agora3/jeff.py` contract, use [[Runtime Guide]]
and [[Implementation Status]].

The shared lesson is durable: never extract OAuth tokens, enumerate the actual
compiled runtime tool inventory, disable inherited host capabilities rather than
asking the model to abstain, and distinguish simulated transport, real runtime
inventory and live account-backed authorship. Alex chose Astra with Agora's own
tools and required OpenAI-account authentication. Companion to [[Executable Components]].

## Account and model

`AGORA_JEFF_PROVIDER=openai-account` uses the official `openai-codex` Python SDK
to control a local Codex app-server. Codex owns sign-in, credential storage and
token refresh. Agora reads account status through the SDK; it never extracts an
access token or substitutes it for an OpenAI API key. Existing Codex ChatGPT
sign-in is reused. Otherwise the protected shell's **Sign in with OpenAI** button
opens Codex's managed browser flow. No logout operation is exposed because this
account is shared with the user's other Codex clients.

The selected model is `gpt-6-astra`. The adapter checks the runtime's available
models and refuses a model substitution. SDK version `0.147.0` ships a runtime
too old for Astra: a live request returned an upgrade-required error. The
integration was verified with Codex **0.153.4**, supplied through the SDK's
supported `codex_bin` option. Set `AGORA_CODEX_BIN` explicitly to that executable.
Recheck the runtime boundary test when upgrading; these dynamic-tool and
environment controls are experimental protocol fields.

```dotenv
AGORA_JEFF_PROVIDER=openai-account
AGORA_JEFF_MODEL=gpt-6-astra
AGORA_JEFF_REASONING=medium
AGORA_CODEX_BIN=/absolute/path/to/current/codex
```

On Windows, use the absolute `.exe` path, not a PowerShell command shim. The
local `.env` is gitignored. Restart Agora after changing it. The chat header shows
**Astra · OpenAI account** when signed in. Account/model access and usage limits
remain those of the signed-in account; this is not unlimited inference.

## What the runtime can access

The adapter starts an ephemeral conversation in an empty temporary directory,
with **no computer environments** and no selected capability roots. It disables
shell tools, file/image tools, web search, JS REPL, other agents, plugins,
host/orchestrator skills, MCP servers, hooks and memory. It overrides coding
instructions with JEFF's instructions. The host's Codex configuration is never
edited. These are capability controls, not a request that the model abstain.

Astra requires Codex's isolated code-mode host to compose tool calls. Its
registered world actions are exactly the Agora verb registry. A runtime test
enumerates the actual nested tools and checks that `process`, `fetch`, `require`,
`exec_command` and `apply_patch` are unavailable. Astra's model catalog also
registers a UTC clock; this is a documented runtime helper, alongside code-mode
execution/wait, and has no world or filesystem access. Do not describe this as
literally zero non-Agora tool names.

All world calls return through `Agent.call`, under the existing dispatch lock,
as actor `jeff`. Kernel validation and recorded events remain authoritative.
Unknown calls, forged actors and calls from another conversation are refused.
The SDK's default approval handler accepts command approvals, so Agora replaces
it with an explicit denial handler. No tool can approve a computer capability.
Credentials and account information are not Agora objects or model context.

## Conversation and control

The OAuth path uses Codex's inner inference loop. Agora controls the available
verbs, dispatch, a limit of 24 Agora tool calls per user turn, a ten-minute turn
deadline, and interruption. It is not the Agents SDK loop with a different token.
Stop blocks later verb dispatch before asking Codex to interrupt; a watchdog
closes an unresponsive transport. Completed changes stay recorded. A provider
failure is reported and the runtime is re-created for the next request.

Conversation state lives in one ephemeral runtime thread until Agora stops.
Fresh desk/selection context is supplied each user turn; within a turn JEFF uses
read/projection verbs and returned results for fresh state. Runtime history may
compact. It is not a durable Agora conversation object, and restarts lose it.
Analytics and persistent conversation history are disabled, but this makes no
claim about all service-side data retention.

Dynamic tools are derived from the stable verb registry. New component actions
can be discovered with `component_actions` and executed with `invoke_component`
immediately, including in the same user turn. Their names do not have to become
new top-level tool definitions. The call pins the admitted source revision.

## Direct API alternative

`AGORA_JEFF_PROVIDER=openai-agents` retains the OpenAI Agents SDK adapter in
`jeff/openai_agent.py`, with `OPENAI_API_KEY` and separate API billing. It uses
Responses, preserves encrypted reasoning and call/output history, refreshes the
projection and derived extension tools between bounded SDK steps, disables
tracing, and uses `store=False`. It has offline SDK and HTTP serialization tests;
it has not been exercised with a live API key here. Anthropic remains supported.
Changing providers requires restarting the server; histories are not translated.

## Verification

`tests/test_codex_agent.py` covers account status/login, continuity, fresh context,
actor attribution, refusals, Stop, finite calls, same-turn action discovery and
replay. `tests/test_codex_runtime.py` runs the actual configured Codex executable
against a local mock inference server. It verifies the effective tool inventory
and absent computer globals without spending model usage or forwarding account
credentials to the mock. Set `AGORA_CODEX_BIN` to include that test in the suite.
Live OAuth evidence and limitations are recorded in the older branch's
`research/holistic-review/astra-harness-validation-2026-09-05.md`; it remains a
historical artifact rather than current Agora3 validation.

Official references: [Codex Python SDK](https://learn.chatgpt.com/docs/codex-sdk),
[account authentication](https://learn.chatgpt.com/docs/auth),
[app-server protocol](https://learn.chatgpt.com/docs/app-server), and
[Astra](https://developers.openai.com/api/docs/models/gpt-6-astra).
