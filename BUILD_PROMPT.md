> **Historical M1 contract.** On September 5, 2026, Alex approved the reliability repairs and personal-lens extension and subsequent executable authorship in `docs/Reference/Personal Lenses.md` and `docs/Reference/Executable Components.md`. M1-only restrictions below describe the initial build, not the approved current scope. M2 onward is an unordered feature horizon in Agora Spec §22. The current public registry may grow deliberately; JEFF tools remain derived from it.

# Build Agora — Milestone One

You are building the first running version of **Agora**: an object-oriented computing
environment layered over stock Linux, with an integrated AI agent called **JEFF**.
This milestone is deliberately small. Its purpose is to prove one thing: *an agent
living in a world of objects, acting through verbs, is observably more capable than
the same model pointed at a filesystem.*

Read `AGENTS.md` before writing any code. It defines the boundaries you must not
cross. The spec documents in `docs/` are the design authority; where this prompt and
the spec disagree, stop and ask.

---

## The one-paragraph architecture

Events are the truth; tables are derived. Verbs are the only writers; projections
are the only compressed readers. The shell is a client. JEFF is a client. The human
at the terminal is a client. All three have identical powers: call verbs, read
projections, read facets under grants. Nothing else exists.

---

## What done looks like

The **acceptance script**, performed live, no code edits mid-demo:

1. Start the shell. An empty desk renders in the browser (a scene entity with zero
   appearances).
2. Tell JEFF (chat panel): *"Put my notes file into the world."* JEFF mints an
   entity with `core.name`, `core.text` (imported from the file), and
   `core.file-backing`; JEFF places it on the desk. An icon appears without a
   refresh.
3. `agora log` in a terminal shows every event of step 2, each carrying
   `actor: jeff`.
4. Edit the text (via `agora attach` or a minimal text lens — CLI is acceptable
   for M1). `agora project <ref> --budget 60` reflects the change.
5. Kill every process. Restart. The desk is exactly as it was. `rebuild` from the
   log produces a byte-identical store.
6. Delete the SQLite file entirely. Restart. The world comes back from the log
   alone.

Every step of that script must also exist as an automated test.

---

## Decisions already made — do not relitigate

These were settled in design sessions. Implement them as stated; record any forced
deviation in `DECISIONS.md` with a reason.

- **Storage**: append-only event log (JSONL, one event per line, fsync on append)
  as truth; SQLite tables derived from it; file bytes stay in the real filesystem
  under the world directory, referenced by hash. A *world* is one directory:
  `log.jsonl`, `store.db`, `blobs/`.
- **Atomicity**: append is all-or-nothing. A verb that fails validation appends
  nothing. Never write a partial line.
- **Text**: `core.text` bodies are CRDT documents (use **Loro**; wrap it entirely
  inside `kernel/text.py` — no Loro type may appear in any other file's signatures).
  Keystrokes are NOT events: edits accumulate in the CRDT and flush to the log as
  one `text-edited` event per burst (idle > 3s or delta > 4KB). The log records
  decisions, not motion.
- **Anchors**: locator = CRDT position-id range + the revision it was created
  against + a short quoted-text fallback. (M1 needs only creation and resolution;
  comments arrive in M2.)
- **Projection tiers**: token budgets `[12, 60, 250, 2000]`. `project.py` exposes
  `select(ref, viewer, purpose, budget)` returning structured facts (attributed,
  with freshness and omissions) and `render_tokens(selection)` returning text.
  The shell's icon/summary labels consume `select()`; JEFF consumes
  `render_tokens(select(...))`. Full-fidelity lens reads do NOT go through
  projection — they use the read verb on raw facets.
- **Verbs for M1**: exactly `mint`, `attach`, `read`, `place`. No find, no copy,
  no move, no forget. `place` writes appearance entries
  `(entity_ref, mode: icon|summary|full, transform)` on the desk scene's facet.
- **JEFF**: a chat loop (Anthropic API) with exactly four tools, one per verb.
  Tool definitions are *derived* from the facet/verb defs in `kernel/facets.py` —
  even though the derivation is trivial now, the tool list must be a projection of
  the registry, not hand-authored strings. Every tool call carries `actor: "jeff"`.
  JEFF's context each turn includes: the desk scene projected at tier 250, and the
  list of available verbs and facet types.
- **Shell**: a thin server (FastAPI or similar) + one page. Server: `GET /tree`
  (desk scene as a declarative render description), `POST /verb` (call a verb),
  and a websocket or SSE channel pushing "scene changed" so the desk live-updates.
  The page renders icons and names. No drag, no editing UI, no styling ambition —
  M1's shell exists to prove the loop, not to be the shell.
- **Snapshot discipline**: the store records `last_applied` event id; boot replays
  only the tail. Full rebuild is a CLI command and a test, not a boot step.

---

## Build order (each stage ends green)

1. `kernel/schema.py` + `tests/test_replay.py` (written first, failing).
2. `kernel/events.py` + `kernel/store.py` until replay-equivalence passes.
   Add `tests/test_atomic.py`.
3. `kernel/facets.py` + `kernel/verbs.py` + `tests/test_verbs.py`.
4. `cli.py` — `agora mint | attach | read | place | log | project | rebuild`.
   From here on, use the CLI to exercise everything manually.
5. `kernel/text.py` + `tests/test_anchors.py` (anchors survive edits above and
   inside the anchored range).
6. `kernel/project.py` + `kernel/scene.py`.
7. `shell/` — tree endpoint, verb endpoint, live update, minimal page.
8. `jeff/` + `tests/test_boundary.py`. Wire the four tools; run the acceptance
   script end to end.

Do not start stage N+1 while stage N has a red test.

---

## Explicitly out of scope for M1

Building any of these is a defect, even if easy: comments and the extension loop
(M2); grants/authority beyond a stub that always allows (leave the two check
functions in `verbs.py` present but permissive, with `# M2:` markers); a `find`
verb; rooms, adapters, reconcilers, WASM, Wayland; any styling of the shell beyond
legibility; JEFF memory beyond the current conversation; multi-world sync.

## Quality bar

Python 3.12, type-hinted throughout, `ruff` clean. Every kernel file ≤ ~200 lines;
if one wants to grow past that, its header sentence has probably become two
sentences — split it and update `AGENTS.md`. Every file opens with the two-line
header (role + never-clause) specified in `AGENTS.md`. Total M1 target: ~1,500
lines excluding tests. When you finish, the acceptance script is the demo; nothing
else needs to exist.
