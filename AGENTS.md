# Agora — Development Guide

Instructions for AI coding assistants and developers working on this codebase.

## What this project is

Agora is an object-oriented computing environment built as a layer over stock
Linux, with an integrated AI agent (JEFF). Entities carry typed facets; verbs are
the only way anything changes; an append-only event log is the source of truth; a
desk scene renders the world for the human while projections render it for JEFF.
The design authority is `docs/`, an Obsidian vault indexed by `docs/Start Here.md`
(especially `docs/Reference/Objects and Facets.md`, and `Agora Spec` §22 for the
roadmap); this file covers how to *work on the code* without fighting that design.

Three axioms shape every decision:

1. **Events are the truth; tables are a cache.** Current state is derived by
   replay. Violating this (writing tables directly) doesn't fail loudly — it rots
   silently: replay stops reproducing reality and every downstream guarantee
   (time travel, undo, provenance) becomes fiction with no error message.
2. **One write path.** All mutation flows through `kernel/verbs.py` into
   `kernel/events.py`. Every future security property (authority modes, grants,
   rate limits) is an edit to one file only because this holds. A second write
   path makes every rule need two implementations, and the system is insecure the
   day one copy lags.
3. **JEFF is a client, not a resident of the codebase.** JEFF acts through verbs
   and perceives through projections — nothing else. Its capability must equal its
   tool list exactly. The moment `jeff/` reaches deeper, the experiment this
   milestone exists to run (is the *world* what makes the agent capable?) is
   unfalsifiable.

## Contribution rubric

### What we want

- **Kernel changes that shrink surface.** Fewer secrets per module, tighter
  never-clauses, invariants promoted into tests.
- **Client capability built from existing verbs.** New CLI subcommands, shell
  affordances, JEFF context improvements that compose `verbs` + `project` calls.
- **Instructive refusals.** Validation errors from the verb layer that tell the
  caller exactly what shape was expected. Refusal quality is part of the security
  layer — JEFF self-corrects from good errors.
- **Tests that state invariants**, not tests that snapshot current behavior.

### What we don't want (rejected even when well-built)

- **Convenience write paths.** Any function outside `verbs.py` that mutates the
  store or appends events, however small ("just for renames").
- **M2+ features arriving early.** Grants logic, extension machinery, a `find`
  verb, shell polish. Scope discipline is the project's survival strategy.
- **Agent scaffolding in `jeff/`.** Retry frameworks, planning layers, memory
  systems. `jeff/` staying tiny is the experimental control.
- **Implementation types leaking across boundaries.** Loro types outside
  `text.py`; SQLite rows outside `store.py`; event records constructed outside
  `events.py`.

## Before you call it a bug — verify the premise

- **"JEFF can't list all entities" is intentional.** M1 navigation is by
  reference from the desk scene projection. Don't add a listing tool; note the
  friction in `DECISIONS.md` instead — accumulated friction is the M2 roadmap.
- **"The shell re-fetches the whole tree on change" is acceptable for M1.**
  Incremental tree diffs are a real feature with a real design (the render-tree
  contract); don't improvise one.
- **"Keystrokes don't appear in `agora log`" is the design.** The log records
  decisions, not motion; fine-grained history lives inside the CRDT body.
- **"`check_authority` always allows" is a stub, not a hole.** It exists so the
  call sites are load-bearing from day one. Marked `# M2:`.

## Capability placement

Choose the highest (least-footprint) rung that solves the problem:

1. **Compose existing verbs in a client** (`cli.py`, `shell/`, `jeff/context.py`),
   with `project` and `scene` for perception. Zero kernel surface.
2. **New facet type in `facets.py`** — when the world needs to *say* something new
   but not *do* anything new. Constitutional defs only in M1; must include
   projection behavior.
3. **New verb in `verbs.py`** — when there's a genuinely new operation. Requires:
   validation, an event kind in `schema.py`, an `apply` branch in `store.py`, a
   test, and a derived JEFF tool. If you're adding a verb, you're probably early —
   check the M1 scope list in `BUILD_PROMPT.md` first.
4. **Change to `schema.py`** — last resort, additive only. Shipped fields are the
   forever format; logs written in week one must replay in year three.

## Project structure

```
agora/
├── BUILD_PROMPT.md      # what M1 is; scope; acceptance script
├── DECISIONS.md         # one dated line per settled question, with the reason
├── docs/                # the design vault (start at Start Here.md) — design authority
├── kernel/
│   ├── schema.py        # event + facet record shapes, as data (~80 lines)
│   ├── events.py        # append + replay; the only log writer (~120)
│   ├── store.py         # SQLite derived from events via apply() (~200)
│   ├── facets.py        # constitutional facet-defs, frozen (~120)
│   ├── verbs.py         # mint/attach/read/place; the choke point (~150)
│   ├── project.py       # select() + render_tokens(); perception (~150)
│   ├── scene.py         # desk scene + appearances (~100)
│   └── text.py          # Loro wrapper; the only file that knows Loro (~120)
├── cli.py               # the object layer without JEFF; also the debugger
├── agora, agora.cmd     # `./agora <command>` runs cli.py under uv
├── shell/               # server.py (tree, verb, chat, change stream) + index.html
├── jeff/                # agent.py loop + tools.py derivation + context.py assembly
├── worlds/              # gitignored; one world = one directory; fork = cp -r
├── tests/               # the four guards, plus verbs, project, cli, shell, jeff, acceptance
├── research/            # review dossiers and archived drafts; history, not design
└── attempt1/            # the superseded first spine attempt; reference only, never imported
```

### File dependency chain

```
schema.py            (no deps — imported by events, store)
   ↑
events.py  facets.py (no deps on each other)
   ↑          ↑
store.py   verbs.py  (verbs → facets + events; NEVER → store for writes)
   ↑
project.py scene.py
   ↑
cli.py  shell/  jeff/   (clients: import verbs + project + scene ONLY)
   text.py              (→ verbs for its one write; used by cli.py, the debugger)
```

An import against this flow is wrong before you've read the code.
`tests/test_boundary.py` enforces the client rule mechanically, and the
kernel chain above as a table. `scene` is on the client list because the desk's
render description is a projection, not judgment; `cli.py` alone may import
`events`, `store`, and `text`, because it is also the debugger — it still
mutates only through verbs.

## Architecture reference

### Event log + store (`schema.py`, `events.py`, `store.py`)

Truth is the ordered sequence of events; the store is a persistent cache of
replay, tracking `last_applied`. `store.apply(db, event)` is the only mutation
path into tables; `rebuild()` derives a fresh store from the log alone.

Invariants:
- `rebuild(world) == world.store` at all times (`test_replay.py` — run it after
  anything that touches these files; the day it fails, stop all other work).
- Append is atomic; a failed verb leaves the log byte-identical
  (`test_atomic.py`).
- Events are never edited or deleted. Corrections are new events.

### Verbs (`verbs.py`, `facets.py`)

The choke point. Order inside every verb: resolve def → validate shape → check
authority (stub) → check grants (stub) → hand a plain intent to `events.append`.
Judgment here, recording there — verbs never construct event records and never
touch the store.

Invariants:
- Every mutation in the system passes through this file (axiom 2).
- Every call carries an authenticated `actor`; it lands in the event and in the
  facet's `written_by`.
- Refusals are instructive and side-effect-free.

### Projection (`project.py`)

Perception for any budgeted consumer. `select()` chooses which attributed facts
survive at a token budget (with freshness and omissions); `render_tokens()`
dresses them as text. The shell's icon/summary labels and JEFF's context consume
the *same* `select()` — divergence is only ever in rendering, never in judgment.
Full-fidelity reads (a lens showing a whole document) bypass projection and use
the read verb on raw facets.

Invariants:
- One selection path. Two selection paths for two consumers is the perception
  version of a second write path.
- Never shorten away uncertainty: an unknown outcome projects as unknown.
- JEFF has no read access that the human lacks; asymmetry is attention
  (defaults), never access.

### Text (`text.py`)

Wraps Loro completely. Exposes: insert/delete by position id, `anchor(start,
end) → Locator`, `resolve(locator)`, `plaintext()`. Edits flush to the log as
one `text-edited` event per burst (idle > 3s or > 4KB) — the log records
decisions, not motion.

Invariants:
- No Loro type in any signature outside this file.
- Anchors survive edits above and inside their range (`test_anchors.py`);
  unresolvable anchors resolve to their recorded revision, never to a wrong
  place.

## Extension points

### Adding a facet type (M1: constitutional only)

1. Add the def to `facets.py`: type id, schema, authority mode, merge class,
   projection behavior, limits.
2. If it needs a new event payload shape, extend `schema.py` *additively*.
3. Add a projection case (or confirm `generic` suffices) in `project.py`.
4. Test: attach → project → replay-equivalence still green.

### Adding a verb (rare — check scope first)

1. Event kind in `schema.py`; 2. verb in `verbs.py` (full validation before
append); 3. `apply` branch in `store.py`; 4. CLI subcommand; 5. derived JEFF tool
(automatic if derivation holds); 6. tests including the atomic-failure case.

### Adding a JEFF tool

Only by derivation from a verb or from `project`. If a desired tool can't be
expressed that way, the kernel is missing a capability — that's a design
conversation, not a tool.

## Policies

**Two-line headers.** Every kernel file opens with: what it is, and what it must
never do. The never-clause is the review criterion for any diff to that file.

**Additive schema only.** New event/facet fields are optional with defaults. A
log written by any past commit must replay on HEAD. There is no down-migration.

**Decisions get written down.** Any settled question — library choice, threshold,
deliberate limitation — gets one dated line in `DECISIONS.md` with the reason.
Code answers "what"; the log answers "when"; only that file answers "why".

**Friction is data.** When JEFF (or you) hits a wall the verbs can't express,
record it in `DECISIONS.md` under "Friction" rather than working around it. The
friction log is the M2 roadmap.

## Known pitfalls

**DO NOT write to SQLite outside `store.apply()`.** Not in a migration, not in a
debug session, not "just once." The store stops being derivable, `test_replay`
fails (if you're lucky), and provenance is fiction. Do this instead: emit an
event through a verb; if no verb fits, that's a design gap to raise.

**DO NOT import `store`, `events`, `schema`, or `text` from `jeff/` or
`shell/`.** This bypasses the choke point and un-runs the experiment.
`test_boundary.py` will fail the build. Do this instead: express the need as a
verb call or a projection; if impossible, raise it.

**DO NOT log high-frequency data as events.** Keystrokes, cursor moves, drag
previews, anything per-frame. The log assumes human-scale decisions
(~10³–10⁴/day). Do this instead: surface state stays in shell memory; text
granularity lives in the CRDT; bulk data goes in `blobs/`.

**DO NOT hand-write JEFF tool definitions.** The tool list is a projection of
the registry in `facets.py`/`verbs.py`. Hand-authored strings drift from the
verbs they describe. Do this instead: extend the derivation.

**DO NOT put interpretation in the shell.** The shell renders trees and forwards
input as verb calls. Logic placed there is invisible to JEFF and to the CLI, and
breaks client equality (axiom 3).

## Testing

```
uv run pytest                       # full suite
uv run pytest tests/test_replay.py  # the conscience — run after ANY kernel change
uv run ruff check . && uv run ruff format .
```

Order of the four guards, and what each protects:

1. `test_replay.py` — truth derives the present (axiom 1).
2. `test_atomic.py` — failure leaves no trace.
3. `test_boundary.py` — clients touch only `verbs`, `project`, `scene`; the kernel
   follows its chain; only `text.py` knows Loro, only `store.py` knows SQLite;
   every kernel file has its two-line header and stays under 230 lines
   (axioms 2, 3).
4. `test_anchors.py` — references survive change.

Then `test_acceptance.py` runs the whole acceptance script from
`BUILD_PROMPT.md` against a scripted stand-in for the model (`tests/fakes.py`).

Good tests state invariants ("rebuild equals store", "a refused attach appends
nothing") against a throwaway world in `tmp_path`. Bad tests snapshot the
current projection text, depend on `worlds/`, or assert on log line formatting.
An invariant that isn't a test is a hope.
