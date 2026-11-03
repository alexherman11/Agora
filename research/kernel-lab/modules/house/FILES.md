# House files

What each file in `research/kernel-lab/modules/house/` does, read from the code (28 October 2026).

## Code

- **`house.py`**: the module itself. It runs the world's agents (people with a `house-agent` thing). It wakes an agent only when someone addresses it, keeps a durable cursor per agent, and posts the agent's words and tool receipts into the chat that woke it. It answers the words `house.who`, `house.wake`, `house.stop`, `house.activity` and `house.log`, and hands `house.build`, `work`, `house.retry`, `house.tell`, `house.review`, `house.land` and `house.manage` on to the builders. It also does the next-steps (continuity) wakes. Entry point: `main()`.
- **`transport.py`**: one long-lived model process per agent. It builds the command line for Claude (`claude -p`, stream-json) and for Codex, writes the MCP config that gives the agent its own see/do/lines door session, and reduces each process's output stream to a few events (`init`, `text`, `tool`, `toolresult`, `compacted`, `result`, `exit`).
- **`builders.py`**: coding workers. `Builders` claims a task card, makes a git worktree, starts a Claude or Codex worker in it under the requester's existing agent session, and takes it through asked → preparing → working → reviewing → landing. Claude and Codex each have their own pool of workers (four of each by default, set in `house-settings`). It also handles follow-ups said in the worker's chat, review, and landing onto main without overwriting other people's uncommitted edits.
- **`manager.py`**: the `house.manage` word. A resident named in a local approval file (`<world>/keep/house-managers.json`, exactly three tasks) can build, tell, retry, review and land those tasks as themselves. The module also writes approved bookkeeping fields back to the card and notifies the manager of receipts once.
- **`charter_hook.py`**: Claude's SessionStart hook after a compaction. It reads the agent's charter (and its task context) again through the door and hands it back as extra context. It never acts.
- **`fake_model.py`**: a scripted stand-in for the Messages API (`HOUSE_FAKE_MODEL`). It answers "On it.", runs one `lines` call taken from `RUN:` in the user's words, then reports the result. It proves the plumbing works and says nothing about what a real model would do.
- **`proof_house.py`**: an end-to-end proof. It runs JEFF in a hidden sandbox desktop (port 8830) against `fake_model.py` and checks the house words, wake rules, the three tools offered, the durable cursor and latency. It writes `evidence/house-proof.json`.

## Tests (pytest, no live model, window or world)

- **`test_builders.py`**: the builder lifecycle: ownership and holds, restart uncertainty, retries, review and landing against a real git repo, Codex progress privacy. Its `manager` fixture is shared by the other tests.
- **`test_builder_capacity.py`**: pool sizes from `house-settings` (default, allowed values 1–4, bad or ambiguous settings refuse) and admission limits.
- **`test_manager.py`**: `manager.py`: approval checks fail closed, no escalation, deduplicated receipts, only approved fields are written.
- **`test_workers.py`**: resident workers: separate Claude and Codex pools, `work` making a card and starting a worker, turns going to the worker's chat, the turn limit, the Claude CLI running in the worktree.

## Notes and records

- **`BUILDERS.md`**: the 27 October design and implementation note for `task.build` / `house.build`.
- **`CONTINUITY.md`**: the task-continuity port (next-steps wakes) onto the kernel.
- **`ACTIVATION-20261027.md`**: the activation record for kernel builders and desktop repairs on kernel8810.
- **`evidence/`**: recorded proof runs: `house-proof.json` (from `proof_house.py`), `activation-20261027.json`, the Rowan worker records of 28 October, and a JEFF chat screenshot.
- **`.gitignore`**: keeps `__pycache__/` and `evidence/fake-model-log.jsonl` out of git.
