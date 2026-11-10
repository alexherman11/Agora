# House files

What each file in `src/agora/modules/house/` does, read from the code (28 October 2026).

## Code

- **`adopt.py`**: steward-only `house.adopt`, dirty-main baseline checks, exact-file commits using repository identity, publication/Git exclusion, and durable `house.adoptions` receipts. `test_adopt.py` uses scratch Git repositories only.

- **`handover.py`**: recoverable `house.hand` transfer. Journals intent before changing the card, recovers the recipient's chat, reconciles the canonical worker owner, and retries completion notices. A pending transfer fences lifecycle changes.

- **`messages.py`**: reads the live Agent Book by heading whenever a message is built. The generic reader is `kernel/text_templates.py`; it uses `Kernel.fill_text`, alongside the existing `$` names. No source template or section cache.

- **`house.py`**: the module itself. It runs the world's agents (people with a `house-agent` thing). It wakes an agent only when someone addresses it, keeps a durable cursor per agent, and posts the agent's words and tool receipts into the chat that woke it. It answers the words `house.who`, `house.wake`, `house.stop`, `house.refresh`, `house.activity` and `house.log`, and hands `house.build`, `work`, `house.retry`, `house.tell`, `house.review`, `house.land` and `house.manage` on to the builders. It also does the next-steps (continuity) wakes. Entry point: `main()`.
- **`transport.py`**: one long-lived model process per agent. It builds the command line for Claude (`claude -p`, stream-json) and for Codex, writes the MCP config that gives the agent its own see/do/lines door session, and reduces each process's output stream to a few events (`init`, `text`, `tool`, `toolresult`, `compacted`, `result`, `exit`).
- **`builders.py`**: coding workers. `Builders` claims a task card, makes a git worktree, starts a Claude or Codex worker in it under the requester's existing agent session, and takes it through asked → preparing → working → reviewing → landing. Claude and Codex each have their own pool of workers (four of each by default, set in `house-settings`); when a pool is full, new workers and follow-ups queue and start by themselves (`start_queued`). It also handles follow-ups said in the worker's chat, `house.stop` and `house.release` for a worker, and `house.land` in one step: checks, landing onto main without overwriting other people's uncommitted edits, then switching the change on (`activate`). A worker whose card moved on or finished ends as released; one a restart cut off recently carries on by itself.
- **`activate_now.py`**: switches a landed change on, detached from the House: runs `kd_reload.py` with the given arguments and logs what it said. `builders.py` starts it after a landing, and again with `house` once nobody is busy when the House itself changed.
- **`manager.py`**: the `house.manage` word. A resident named in a local approval file (`<world>/keep/house-managers.json`, exactly three tasks) can build, tell, retry, review and land those tasks as themselves. The module also writes approved bookkeeping fields back to the card and notifies the manager of receipts once.
- **`charter_hook.py`**: Claude's SessionStart hook after a compaction. It reads the agent's charter (and its task context) again through the door and hands it back as extra context. It never acts.
- **`fake_model.py`**: a scripted stand-in for the Messages API (`HOUSE_FAKE_MODEL`). It answers "On it.", runs one `lines` call taken from `RUN:` in the user's words, then reports the result. It proves the plumbing works and says nothing about what a real model would do.
- **`proof_house.py`**: an end-to-end proof. It runs JEFF in a hidden sandbox desktop (port 8830) against `fake_model.py` and checks the house words, wake rules, the three tools offered, the durable cursor and latency. It writes `evidence/house-proof.json`.

## Tests (pytest, no live model, window or world)

- **`test_handover.py`**: real hidden kernel receipts, repeated chat creation, partial handoffs, lost responses, restart/save recovery, ownership admission, concurrent calls, and the ten-second accepted-call deadline.

- **`../../tests/test_house_refresh.py`**: fresh conversations on demand: current prompt, charter, welcome, guide and soul; preserved transcript and old state; sleeping and busy agents; queued messages and restart recovery; both transport commands; stale child events; failure handling; steward-only Lines dispatch.
- **`test_builders.py`**: the builder lifecycle: ownership and holds, restart uncertainty, retries, review and landing against a real git repo, Codex progress privacy. Its `manager` fixture is shared by the other tests.
- **`test_builder_capacity.py`**: pool sizes from `house-settings` (default, allowed values 1–4, bad or ambiguous settings refuse) and admission limits.
- **`landing_control.py`**, **`landing-defaults.json`**: world-configurable deadlines, cancellable lock/process waits, and safe fencing when child termination is denied.
- **`test_ghost_landing.py`**: immediate attempt receipts, real kernel owner-write refusal, requester/owner wakes, crash recovery, cancellation and import-lock isolation.
- **`test_manager.py`**: `manager.py`: approval checks fail closed, no escalation, deduplicated receipts, only approved fields are written.
- **`test_levers.py`**: the 4 Nov levers: stop and release a worker, a worker whose card moved on or finished ends released, one-step landing (and checking again when main moved), the House restarting itself only when nobody is busy.
- **`test_workers.py`**: resident workers: separate Claude and Codex pools, `work` making a card and starting a worker, turns going to the worker's chat, the turn limit, the Claude CLI running in the worktree.

## Notes and records

- **`MESSAGES.md`**: the heading and fill-in contract, missing-section behavior, and hidden evidence for the Agent Book migration.

- **`BUILDERS.md`**: the 27 October design and implementation note for `task.build` / `house.build`.
- **`CONTINUITY.md`**: the task-continuity port (next-steps wakes) onto the kernel.
- **`ACTIVATION-20261027.md`**: the activation record for kernel builders and desktop repairs on kernel8810.
- **`evidence/`**: recorded proof runs: `house-proof.json` (from `proof_house.py`), `activation-20261027.json`, the Rowan worker records of 28 October, and a JEFF chat screenshot.
- **`.gitignore`**: keeps `__pycache__/` and `evidence/fake-model-log.jsonl` out of git.
