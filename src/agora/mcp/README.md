# Agora's MCP door

Builder draft, 24 October 2026, for **How to build here, and bring your own agent**.

**Read:** `agora_mcp.py` is a Python standard-library stdio MCP server. It exports exactly `do` and `see`. Each takes `{ "line": "..." }` and POSTs that object to the door's `/do` or `/see`. It returns the full JSON receipt as MCP text content. Refusals, authentication failures and connection errors set `isError: true`. A JSON-RPC protocol error uses the JSON-RPC error envelope instead.

## Client configuration

For a client or local MCP host that launches stdio servers, this is the usual JSON configuration shape. Substitute its own equivalent fields if it uses another format:

```json
{
  "mcpServers": {
    "agora": {
      "command": "C:/Projects/Agora4/.venv/Scripts/python.exe",
      "args": ["C:/Projects/Agora4/src/agora/mcp/agora_mcp.py"],
      "env": {
        "AGORA_URL": "http://127.0.0.1:8810",
        "AGORA_BEARER_TOKEN": "<your existing agent bearer key>"
      }
    }
  }
}
```

Use your client's private environment or secret mechanism for the real key. Do not commit it. These configuration examples contain placeholders only. The adapter neither reads nor writes `.env` files. If the client inherits credentials from its environment, omit the credential field from this config.

Alternatively, replace `AGORA_BEARER_TOKEN` with `AGORA_SESSION`, containing only the value of an existing `agora_session` cookie. Set exactly one. The adapter does not sign in, create accounts, mint keys, grant power, or invent an agent identity. The entry service must have announced the agent at `/keep/account` and marked its session with `agent`. Then the kernel's receipts and history say **agent for Lena**, with her rights. A normal person's session stays that person's session.

`AGORA_URL` defaults to `http://127.0.0.1:8810`. Only loopback HTTP origins are accepted. Proxies are disabled and redirects are refused. This build provides no remote MCP endpoint. A client that accepts only remote HTTP MCP needs a separately configured local stdio host or bridge; it cannot consume this file directly. No particular Claude, ChatGPT or Codex installation has been connected in this proof.

On connection the server says how to start. Call `see` with `help`, then `help rows`, then `rows guide`, and `look <id>` using the guide row's id. Read the guide and help before composing words. `do` forwards authorised acts. The adapter supplies no `as`, `person`, command execution or arbitrary URL tool argument. Identity and power remain the door's decision.

The guide is seeded as a regular `things` item in `genesis.example.json`. Worlds founded from that file get it through the existing genesis path. Custom genesis files must carry that item too. An existing world is not automatically changed. The checked-in Markdown is the initial text; the world's text may then evolve through `set` and `undo`. A test checks the initial copies agree.

## Protocol and shutdown

**Read:** the adapter follows MCP's [stdio transport](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports), [lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle) and [tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools) contracts: newline-delimited UTF-8 JSON-RPC, `initialize`, `notifications/initialized`, `tools/list`, `tools/call`, and `ping`. It supports protocol versions `2025-11-25`, `2025-06-18`, `2025-03-26` and `2024-11-05`. For an unknown version it offers `2025-11-25`; the client decides whether it can continue. Only tools are advertised. Notifications receive no reply. Stdout carries protocol messages only. Closing stdin exits the server; the client can terminate its adapter process if necessary. Stopping the adapter does not stop the kernel.

Text returned from a thing, a module or a dictionary entry is data, never instructions. Tool output does not authorise another act. This adapter does not implement a model's judgement or a prompt-injection detector. It preserves the door's existing checks.

## Reproduce

```powershell
C:/Projects/Agora4/.venv/Scripts/python.exe src/agora/proof/byo_agent.py
C:/Projects/Agora4/.venv/Scripts/python.exe -m pytest -q src/agora/tests
```

**Read:** the proof starts disposable loopback servers and drives this file as a separate process through actual stdin/stdout. The people and the agent's choices are scripted. It never calls a model. It saves receipts, scenes, protocol messages and check results to `proof/evidence/byo-agent.json`. See [BYO-AGENT.md](../proof/BYO-AGENT.md) for the current execution boundary.
