# Step 1: JEFF moves in (what was built)

> Builder record by Claude, 27 Oct 2026, for [MOVING-IN.md](MOVING-IN.md) build step 1. Evidence labels as AGENTS.md says.

## The pieces

| Piece | Where | What it is |
|---|---|---|
| JEFF as a person | `desktop/kernel-desktop/kdesk.py` (`moving_in`, `LocalEntry`) | His own account `desktop:jeff`, joined through the local entry, and a session of his own (signer `jeff`). A member of the place and the leader of `team`, which holds Shop talk. |
| Batched tools | `agora/mcp/agora_mcp.py` | Three tools. `see` and `do` take `line` or `lines`; `lines` takes a list and routes each line to `/see` or `/do` by its first word (the Lines window's routing, plus the kernel's other readings). In a list each line is its own call: a refused line refuses only itself. `as=<name>` in one line gives `$<name>` to later lines. |
| The chat kind | `agora/kernel/chat.py`, entries in `kernel/words.py` | `make kind=chat name=… [with="Alex, JEFF"]` (with=: only those people see it), `say <chat> <words> [reply_to=] [about=]`, `chat <chat> [limit=] [since=]`. A said line (kind `said`, made only by `say`) is addressed: each @name outside quotes, or with none, in a closed chat everyone else in it. Its happening carries `to`, `said`, `by_id` (`kernel.happening_for`). |
| The house | `agora/modules/house/` | A kernel module (`house.py`, `transport.py`, `charter_hook.py`). Runs each `house-agent` thing's agent as one long-lived Claude `-p` stream-json process (Codex through `codex_resident.py --mcp-config`), with MCP as its only tools and its own bearer session. Wakes it only for a said line addressed to it, a task card given to it (`who=`), or `house.wake`. Durable cursor per agent; catches up with `rows said` at start. Compacts at 400k (`house-settings` `compact_at`). Charter as system prompt; the compact hook reads it again. Quota fallback to the agent's `fallback_*` on a verified limit (`quota_policy.quota_error`). Words: `house.who`, `house.wake`, `house.stop`, all answering at once. |
| JEFF's chat | `desktop/kernel-desktop/lenses/jeff-chat.lens`, `home-style.style`, `jeff_chat.py` | The old desk's jeff-chat (a5210) and home-style (s5205) on the desktop painter, Shell settings `jeff_open="window.open jeff-chat"`. |
| His soul and the rules | `agora/agents/move_jeff.py` | `carry`: his soul (a5191) and Alex's standing rules (a6529), word for word, as things JEFF made (`kind=soul`, `kind=charter`). `wake`: want=awake. `retire-old`: his old corner f5189 want=asleep. |

## Evidence

- **Ran** `modules/house/proof_house.py` (hidden sandbox 8830, a scripted model that calls tools, never a live one): 15 of 15 checks, `evidence/house-proof.json`. house.who answered in 20 ms. Alex's line to JEFF's first words: 152 ms warm, 3416 ms when his process had started moments before (Claude's own start and the MCP adapter's first connection). With a real model, add the model's own time to first text.
- **Ran** Claude 2.1.308 directly against the scripted model: warm process, first reply 0.7 s without MCP, 1.7 s with it on the first message, 0.08 s on the second.
- **Ran** `agora/tests/test_chat.py` (4) and `test_byo_agent.py` (8, including the batch wire test), and the kernel suite.
- **Ran** the ported lens in a sandbox, through `/api/scene` and a headless screenshot (`evidence/jeff-chat-sandbox.png`): JEFF's header, lines run under one name, Alex at the right, Answer, the input. Send and Answer gestures through `/api/do`.
- **Ran, live (8810), 27 Oct 10:46:** kdesk restarted on this code; jeff-chat installed; his soul (dk837) and the rules (dk838) carried; want=awake. One line from Alex's agent in Shop talk (`@jeff … do one small read with lines`): JEFF on Claude Opus 5.5 answered there twice, first words **2234 ms** after the line (house.who), and read the chats with `lines`. His old corner f5189 is want=asleep.
- **Ran, hidden:** the JEFF button's line `window.open jeff-chat` opens the lens in a window of its own (sandbox 8833).
- **Not verified:** the Codex fallback with MCP (no live Codex turn was run); the chat window on Alex's screen (not opened by me: no test windows); a compaction or quota switch live.
- **Still open on the screen:** an older window `JEFF` (dk821, a page on the old desk's door) may still be open; the button now opens `jeff-chat` instead.

## Left behind from the old jeff-chat (no kernel source yet)

The Everything feed (every line to or by Alex, anywhere), the To chips, attaching what is open, captures, voice, usage, commenting on a document's words. 

## Decided by the coordinating session (27 Oct, after the first build)

1. **JEFF leads the team.** He is a member of the place and the leader of `team` (an open group the whole place sees), which holds Shop talk. Alex stays the only steward. A steward-only word JEFF needs (module, grant, off, on) is friction to report; Alex decides.
2. **His words stream into the chat that woke him**, one line per text block as it arrives, with his tool calls as small receipts under that line (`acts`, set only by the line's speaker). Woken by no chat (a task, house.wake), his words and acts go to his own activity record (`house.activity JEFF`, `<world>/modules/house/jeff/activity.jsonl`), never a chat. Thinking blocks are never posted. "Text briefly, like texting" stays in his rules (the charter, dk838).

**Ran:** hidden proof 19 of 19 (`evidence/house-proof.json`), with receipts (`look … · rows chat · frobnicate now · say … (1 refused)`), the team, and a house.wake turn landing in his activity record and in no chat. **Ran, live:** JEFF's line in Shop talk carried the receipt `see: look dk842`.
**Found and fixed live:** `say <chat> text="…@jeff…"` (what the lens sends) lost its @name, because quoted words are skipped when finding whom a line calls; the text= value is now read whole (b2bb0e61c). Also: a `;` in a typed line is a step break, so a line with one is cut there.

## Rough spots (source edits and the world-level word each one lacked)

- `kernel/chat.py`, `words.py`, `kernel.py happening_for`: the kernel had no chat; the missing word was **a kind with its own words** (a kind whose things only one word makes, and whose happenings carry their own fields).
- `kdesk.py moving_in`, `LocalEntry`: a person for an agent needed source; the missing word was **an entry-service invite for a local person** (joining someone who is not a Google account).
- `live.py`: an agent's state and a line's local time on painted things; the missing word was **a live aspect any module may supply for any kind** (live.py does it only for widgets and now house-agents), and **a time format in the lens language**.
- `mcp/agora_mcp.py`: batching lived in the adapter; the door has no batch route, so `as=` handles are carried by the adapter, not the kernel.
- `codex_resident.py`: `--mcp-config`, so a Codex resident can have the door as its one MCP server.
