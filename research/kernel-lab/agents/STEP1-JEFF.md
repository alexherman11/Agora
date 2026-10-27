# Step 1: JEFF moves in (what was built)

> Builder record by Claude, 27 Oct 2026, for [MOVING-IN.md](MOVING-IN.md) build step 1. Evidence labels as AGENTS.md says.

## The pieces

| Piece | Where | What it is |
|---|---|---|
| JEFF as a person | `window-lab/kernel-desktop/kdesk.py` (`moving_in`, `LocalEntry`) | His own account `desktop:jeff`, joined through the local entry, and a session of his own (signer `jeff`). A **member** of the place. Not yet a leader: see *Open* below. |
| Batched tools | `kernel-lab/mcp/agora_mcp.py` | Three tools. `see` and `do` take `line` or `lines`; `lines` takes a list and routes each line to `/see` or `/do` by its first word (the Lines window's routing, plus the kernel's other readings). In a list each line is its own call: a refused line refuses only itself. `as=<name>` in one line gives `$<name>` to later lines. |
| The chat kind | `kernel-lab/kernel/chat.py`, entries in `kernel/words.py` | `make kind=chat name=… [with="Alex, JEFF"]` (with=: only those people see it), `say <chat> <words> [reply_to=] [about=]`, `chat <chat> [limit=] [since=]`. A said line (kind `said`, made only by `say`) is addressed: each @name outside quotes, or with none, in a closed chat everyone else in it. Its happening carries `to`, `said`, `by_id` (`kernel.happening_for`). |
| The house | `kernel-lab/modules/house/` | A kernel module (`house.py`, `transport.py`, `charter_hook.py`). Runs each `house-agent` thing's agent as one long-lived Claude `-p` stream-json process (Codex through `codex_resident.py --mcp-config`), with MCP as its only tools and its own bearer session. Wakes it only for a said line addressed to it, a task card given to it (`who=`), or `house.wake`. Durable cursor per agent; catches up with `rows said` at start. Compacts at 400k (`house-settings` `compact_at`). Charter as system prompt; the compact hook reads it again. Quota fallback to the agent's `fallback_*` on a verified limit (`quota_policy.quota_error`). Words: `house.who`, `house.wake`, `house.stop`, all answering at once. |
| JEFF's chat | `window-lab/kernel-desktop/lenses/jeff-chat.lens`, `home-style.style`, `jeff_chat.py` | The old desk's jeff-chat (a5210) and home-style (s5205) on the desktop painter, Shell settings `jeff_open="window.open jeff-chat"`. |
| His soul and the rules | `kernel-lab/agents/move_jeff.py` | `carry`: his soul (a5191) and Alex's standing rules (a6529), word for word, as things JEFF made (`kind=soul`, `kind=charter`). `wake`: want=awake. `retire-old`: his old corner f5189 want=asleep. |

## Evidence

- **Ran** `modules/house/proof_house.py` (hidden sandbox 8830, a scripted model that calls tools, never a live one): 15 of 15 checks, `evidence/house-proof.json`. house.who answered in 20 ms. Alex's line to JEFF's first words: 152 ms warm, 3416 ms when his process had started moments before (Claude's own start and the MCP adapter's first connection). With a real model, add the model's own time to first text.
- **Ran** Claude 2.1.308 directly against the scripted model: warm process, first reply 0.7 s without MCP, 1.7 s with it on the first message, 0.08 s on the second.
- **Ran** `kernel-lab/tests/test_chat.py` (4) and `test_byo_agent.py` (8, including the batch wire test), and the kernel suite.
- **Ran** the ported lens in a sandbox, through `/api/scene` and a headless screenshot (`evidence/jeff-chat-sandbox.png`): JEFF's header, lines run under one name, Alex at the right, Answer, the input. Send and Answer gestures through `/api/do`.
- **Not verified:** the Codex fallback with MCP (no live Codex turn was run); a live Claude turn before JEFF himself went live.

## Left behind from the old jeff-chat (no kernel source yet)

The Everything feed (every line to or by Alex, anywhere), the To chips, attaching what is open, captures, voice, usage, commenting on a document's words. JEFF's acts are not yet shown as receipts under his line (the page's mock); the house keeps his last acts in `house.who`.

## Open (asked of the coordinating session, not answered when this was written)

1. "JEFF is a leader": a leader of the place is a steward in the kernel. He is a member for now; `role <jeff> leader in=<group>` makes him a leader of a group when that is settled.
2. His plain words: `speaks=text` (the default) says his turn's text into the chat that woke him as he writes it. `set <house-agent> speaks=say` makes only his own `say` lines reach a chat.

## Rough spots (source edits and the world-level word each one lacked)

- `kernel/chat.py`, `words.py`, `kernel.py happening_for`: the kernel had no chat; the missing word was **a kind with its own words** (a kind whose things only one word makes, and whose happenings carry their own fields).
- `kdesk.py moving_in`, `LocalEntry`: a person for an agent needed source; the missing word was **an entry-service invite for a local person** (joining someone who is not a Google account).
- `live.py`: an agent's state and a line's local time on painted things; the missing word was **a live aspect any module may supply for any kind** (live.py does it only for widgets and now house-agents), and **a time format in the lens language**.
- `mcp/agora_mcp.py`: batching lived in the adapter; the door has no batch route, so `as=` handles are carried by the adapter, not the kernel.
- `codex_resident.py`: `--mcp-config`, so a Codex resident can have the door as its one MCP server.
