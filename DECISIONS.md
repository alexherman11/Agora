# Decisions

One dated line per settled question, with the reason. Code answers "what"; the
log answers "when"; only this file answers "why". Newest at the bottom of each
section. A decision that changes gets a new line, never an edit.

## Settled

- **2026-09-03 — Restart.** Milestone One is rebuilt from scratch on the `docs`
  branch under `BUILD_PROMPT.md` and `AGENTS.md`. The earlier spine attempt
  (`agora/`, its `tests/`, `pyproject.toml`) is superseded and was never
  committed; it now lives under `attempt1/` for reference (its own notes are in
  `attempt1/agora/README.md`) and is not part of the build. Reason: M1 tests one
  claim with the smallest possible surface, and the old layout carried
  reconcilers, brokers, lenses, and a portal that are M2+ features.
- **2026-09-03 — Storage.** Append-only JSONL event log (one event per line,
  fsync on append) is the truth; SQLite tables are derived by replay and record
  `last_applied`; file bytes live in the real filesystem under the world
  directory, referenced by hash. A world is one directory: `log.jsonl`,
  `store.db`, `blobs/`. Reason: replay must reproduce reality from the log alone
  (Spec §11, Objects §10); a directory makes fork `cp -r`.
- **2026-09-03 — Atomicity.** Append is all-or-nothing; a verb that fails
  validation appends nothing; never a partial line. Reason: a refused action
  must leave no trace, or provenance is fiction.
- **2026-09-03 — Text.** `core.text` bodies are Loro CRDT documents, wrapped
  entirely in `kernel/text.py`; no Loro type in any other file's signatures.
  Edits flush as one `text-edited` event per burst (idle > 3 s or delta > 4 KB).
  Reason: the log records decisions, not motion (Spec §11); one file knowing
  Loro keeps the CRDT replaceable.
- **2026-09-03 — Anchors.** Locator = CRDT position-id range + the revision it
  was created against + a short quoted-text fallback. M1 needs creation and
  resolution only. Reason: Objects §2.3 requires a locator that survives edits
  and resolves to its old revision rather than a wrong place.
- **2026-09-03 — Projection.** Tiers `[12, 60, 250, 2000]`.
  `select(ref, viewer, purpose, budget)` returns attributed facts with freshness
  and omissions; `render_tokens(selection)` returns text. The shell's labels and
  JEFF's context share `select()`; full-fidelity reads use the read verb.
  Reason: one selection path (Objects §7); two would be a second write path for
  perception.
- **2026-09-03 — Verbs.** Exactly `mint`, `attach`, `read`, `place`. No find,
  copy, move, or forget in M1. `place` writes appearance entries
  `(entity_ref, mode: icon|summary|full, transform)` on the desk scene's facet.
  Reason: scope discipline; position belongs to appearances (Spec §5).
- **2026-09-03 — Authority.** `check_authority` and `check_grants` exist in
  `verbs.py`, always allow, and are marked `# M2:`. Reason: the call sites must
  be load-bearing from day one so M2 is an edit to one file.
- **2026-09-03 — JEFF.** A chat loop on the Anthropic API with exactly four
  tools, one per verb, derived from the registry in `kernel/facets.py` and
  `kernel/verbs.py`, never hand-authored. Every call carries `actor: "jeff"`.
  Context each turn: the desk scene at tier 250 plus the list of verbs and facet
  types. Reason: JEFF is a client; its capability must equal its tool list.
- **2026-09-03 — Shell.** A thin server (FastAPI or similar) with `GET /tree`,
  `POST /verb`, and a websocket or SSE "scene changed" channel, plus one page
  that renders icons and names. No drag, no editing UI, no styling. Reason: the
  M1 shell proves the loop; it is not the shell.
- **2026-09-03 — Snapshot discipline.** Boot replays only the tail after
  `last_applied`; full rebuild is a CLI command and a test, not a boot step.
  Reason: boot stays fast; rebuild stays provable.
- **2026-09-03 — Quality bar.** Python 3.12, type-hinted, `ruff` clean, every
  kernel file ≤ ~200 lines with a two-line header (role + never-clause), ~1,500
  lines total excluding tests. Reason: a file that outgrows its header sentence
  has two jobs.
- **2026-09-03 — Docs layout.** `docs/` is an Obsidian vault arranged by
  authority tier (`docs/Start Here.md`). `AGENTS.md` was adjusted to cite the
  real paths (`docs/Reference/Objects and Facets.md`) rather than
  `docs/Objects_and_Facets.md`. Spec §22 is the maintained roadmap: M1 first,
  then the six-step spine.

## As built (M1)

Choices made while writing the code, where `BUILD_PROMPT.md` left room.

- **2026-09-03 — Ids.** `ent_`/`evt_` + 10 base32 chars of milliseconds + 16
  random chars, minted in `events.py`. Not a strict ULID; sortable enough to read
  a log, content-free, never reused. An event's `seq` is its line number,
  assigned at replay and never serialized, so appends need no read and no lock.
- **2026-09-03 — Torn lines.** A line that is not JSON can only be an append
  that died mid-write. Replay skips it wherever it is (it keeps its `seq`); the
  next append seals it with a newline. A JSON line missing fields is corruption
  and raises. Reason: the log is never edited, and a torn write is the one
  failure that must be survivable without a repair tool.
- **2026-09-03 — Store equality.** "Byte-identical store" is checked as a
  canonical dump of every table (`Store.snapshot()`), not SQLite file bytes,
  which vary with page layout. `agora rebuild` prints `identical` or `DIVERGED`.
- **2026-09-03 — One intent, several effects.** `mint` may carry initial
  facets; the log records one `entity-minted` event with them (Objects §10.2).
  `attach` on an existing `core.text` records `text-edited`; the first attach
  records `facet-attached`.
- **2026-09-03 — The desk.** One desk per world with the fixed id `ent_desk`,
  minted lazily by `verbs.ensure_desk` as actor `system`. An id is a name.
- **2026-09-03 — File import is the verb's job.** `core.text {"path"}` resolves
  to `{"text"}` at attach; `core.file-backing {"path"}` gains `hash` and `size`
  and copies the bytes to `blobs/<hash>`. The logged body is self-contained, so
  JEFF needs no file tool and replay needs no filesystem.
- **2026-09-03 — Text and anchors.** The facet body carries both `text` and a
  base64 Loro `snapshot`; the store never decodes it. If a plain `{"text"}` is
  attached after a snapshot, the text wins. An anchor's head cursor rides the
  first character of the range and its tail the character after it, so an edit
  inside stretches the range and deleting the range unseats the head, which
  resolves to the recorded revision.
- **2026-09-03 — Projection.** Rank: name and scene, then file, then text.
  Purpose `label` keeps only the name (an icon names; a summary summarizes).
  Trust classes are two: written by the viewer, or not; the latter renders
  `(by <writer>)`. Truncated text ends in `…` and is never silently dropped.
- **2026-09-03 — `scene` is client-importable.** Clients may import `verbs`,
  `project`, and `scene`; the desk's render tree is a projection, not judgment.
  `cli.py`, being the debugger, may also import `events`, `store`, and `text`.
- **2026-09-03 — One store, two threads.** The shell serves `/verb` on the
  event loop and runs JEFF in a worker thread over one SQLite handle
  (`check_same_thread=False`); every read syncs first and SQLite serializes.
- **2026-09-03 — Results over the wire.** A minted id becomes `{"entity": id}`
  in tool results and in `/verb` responses, so every result is an object.
- **2026-09-03 — Who you are.** The actor at the terminal and the viewer at the
  page are the same name: `AGORA_ACTOR`, else the OS user. The CLI projects as
  the actor unless `--viewer` says otherwise.
- **2026-09-03 — JEFF's model.** Default `claude-sonnet-5` (the Spec leans
  Sonnet-class for day one); `AGORA_JEFF_MODEL` overrides. Without credentials
  the shell runs and `/chat` answers 502 with the reason.
- **2026-09-03 — Credentials.** The shell loads `.env` (gitignored) at start,
  never overriding the environment; nothing else reads it. JEFF's provider is
  reached through the Anthropic SDK's own `ANTHROPIC_BASE_URL`, so OpenRouter's
  Anthropic-compatible `/api/v1/messages` works with no code path of its own
  (verified: it accepts `x-api-key`). Day-one model for the demo:
  `anthropic/claude-haiku-4.5`, cheap and good with tools.

## Friction

When JEFF or a developer hits a wall the verbs cannot express, record it here
rather than working around it. Each line: date, who hit it, what was attempted,
what the verbs could not say. This list is the M2 roadmap.

- **2026-09-03 — Claude, building M1.** Nothing can leave the desk: `place`
  replaces an appearance but no verb removes one. Wanted for a tidy demo;
  deferred (a `forget`/detach family is M2, Objects §4.6).
- **2026-09-03 — Claude, building M1.** JEFF cannot read a file it has not
  imported, and cannot list entities that are not on the desk. Both are the
  design (navigation is by reference); noted so the M2 roadmap sees them.
- **2026-09-03 — Alex, first use.** The interface is rough: the chat log has
  no scroll region so the panel slides down, and every `place` without a
  transform lands at (0, 0), so notes stack on top of each other (JEFF never
  picks coordinates). Nothing on the desk is a lens; `full` mode is still a
  projection. Alex wants to develop the interface and add tools from inside
  JEFF. Agreed direction, in order: fix the chat log and give the desk a
  free-slot placement policy (client only); a real text lens over the read
  verb, which forces a decision on how browser edits reach the CRDT; lenses as
  entities rendered in sandboxed frames with a read/emit/state bridge; JEFF
  authoring lenses with the four verbs it has; facet definitions as entities;
  then handlers under grants (the spine); then the repository itself as
  objects (Spec §16). Alex has corrections to this plan still to come.
