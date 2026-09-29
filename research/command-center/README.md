# The command center

Started 2026-09-28 at Alex's direction. The first home application: a place inside Agora where Alex lives and works with a small team of resident agents, built entirely from Agora's primitives and restylable from inside Agora. The build is also the way Agora improves: when it hits friction, we stop, fix Agora properly, record it in [FRICTION.md](FRICTION.md), and go on. No stopgaps.

Builder: Claude (the teaching session), from outside at first; the residents are meant to take it over from inside.

## Decisions (Alex, 28 Sep)

- **Three new residents.** No coordinator; the old team (Sable, Pike, Juniper, Jeff) is paused and not migrated. Alex is the leader; residents may message him, and each may lead its own disposable workers (later).
  - *29 Sep, Alex:* Sable, Pike and Juniper are **born again** as the three residents: the same names, reset. Corners f571, f576 and f581 carry `actor=sable|pike|juniper`, and each holds a note "Born again, 29 Sep" pointing back. Their first corners (f276, f279, f273) are kept in a new Archive (f615) in Home, each with a note pointing forward. Their tasks are kept with `owner` removed, and waits on them are dropped. Old events still carry the bare names, since the log is never rewritten. Heading (a159) records it. Jeff stays paused. (World events e590 to e632, by claude.)
- **No system prompt from the harness.** Each resident runs as `claude -p` with an empty system prompt, no tools, no settings, no auto-memory. Everything it knows comes from the world. Its soul is a note in its own corner: it names itself on its first pass and rewrites the soul to begin "I am ...", and keeps growing it.
- **No tool at all.** The house relays: whatever the resident writes, lines that begin with a desk command are done in the world as that resident; the desk's reply is the next message. Any other line is the resident's own thinking. Talking to someone is a desk act (a chat line, a note). The MCP desk tool (`desk_mcp.py`) stays as an optional mode.
- **Objectives on the Board.** While an objective is open the residents work continuously; otherwise they wake every 4 hours, or when someone speaks to them.
- **Nothing reaches Alex's phone yet. No usage guardrail yet.**

## Decisions the builder made (revisable)

- **Intent in the world, a house outside it.** The world holds what is wanted (a resident's `want=awake|rest`, messages, objectives); the house, a host process (`research/text-desk-lab/notation/house.py`), makes it so and writes back what it observes as actor `house`. Replay never wakes anyone.
- **Observed status changes are events; heartbeats are not.** The house writes `status` only when it changes. Liveness, usage and the activity pulse live in the house's own state and reach lenses as a host row source with its age printed, so a dead house looks dead and the history stays meaningful.
- **Transcripts live outside the world**, in the house's state folder; the world holds what matters from them (messages, status, a line per turn) and a pointer.
- **One world.** The command center is a room in `frontier`, beside Home, so it can link corners, the Board and the Handbook.
- **Names are minted at the door.** A new resident's first act is to choose its name; that name is its desk identity from then on (identity is minted once, never reused). Renaming later is an open question, recorded as friction.

## Where things are

- `research/text-desk-lab/notation/house.py`: the house.
- `research/text-desk-lab/notation/fake_model.py`: a scripted stand-in for the Messages API, for testing the loop without a model. Scripted output proves the plumbing, never a model's behavior.
- `research/command-center/DRAFT-living-in-the-world.md`: a draft (28 Sep) on residents living in the world MOO-style rather than reading the screen; how their reaches are handled is left open.
- `research/command-center/FRICTION.md`: every place the build pushed back, and what was done about it.
- `research/text-desk-lab/notation/try_house.py`: the trial bench (Alex, 28 Sep: "real, but disposable `claude -p` sessions for testing"). It copies a world to a throwaway `try-<tag>`, wakes chosen corners, runs the real house, can speak as Alex, caps turns and time, writes a report to `trials/<tag>.md`, then deletes the world, its house state and the residents' claude conversations. Its reports record what a model wrote; they are evidence for one run, not for the design.
- `research/command-center/seed/`: the pixel style and the command-center lens as first installed (`install.py` seeds a world). The world's copies are the live ones: restyle the porch by editing the `pixel` note in the Porch.
- The house's state: `research/text-desk-lab/notation/house-state/<world>/` (house.json, and per corner state.json, transcript.jsonl, stderr.log). claude keeps each resident's conversation itself, under `~/.claude/projects/<that corner's folder, flattened>`; if it is lost, the resident starts fresh from the world (F15).
- The house runs the newest `claude` it finds (on PATH or kept by the desktop app), or `$HOUSE_CLAUDE`: the standalone 2.1.173 on PATH refuses Opus 5.5.

## Residents' days (29 Sep, Alex)

- **Thinking isn't resting.** A reply of only thinking is answered `(quiet)` (or with waiting news); a resident rests when it says `> rest` (until someone calls) or `> rest 2 hours` (human time, a month at most). A call reaches it at once, resting or not. After 10 quiet exchanges in a row the house lets it rest (F26).
- **Every wake begins with who it is:** `You are <name>. Your corner is <id>.`, then its own wake lines as before.
- **The Handbook goes with them.** `handbook` (or `hb`), a house verb (a608), shows the whole shelf from anywhere. The binder *What we're building* carries Agora and Dynamic Desk, copied verbatim from `docs/` by `notation/handbook_docs.py` (the docs stay the source; run it after they change).

## Drafts and the lesson

- `DRAFT-living-in-the-world.md` (a595) and `DRAFT-three-ways-to-change-the-world.md` (a598), both part of the task *Restructuring the desk* (a593).
- `LESSON-how-the-desk-grows.html`: the walkthrough of live building, published for Alex.

## Live building (28 Sep, Alex: "the two tier live world, and the workers")

Two tiers. What can be made in the world is made there, at once. What needs host code goes through a worker and git.

- **Tier 1, world verbs** (`notation/verbs.py`; inside the desk, `help verbs`). A verb is a note tagged `verb`:
  - its title is the word (aliases with `|`), and its text is desk lines with `$1 … $* $1.title $me $this`;
  - it has no `on` while its maker carries it as a draft, `on=<id>` to sit on a thing, and `on=house` for everyone;
  - lookup goes carried, then the named thing, then the house, and ambiguity at one level refuses;
  - `use <id> …` runs one verb exactly;
  - a verb runs as whoever invokes it, stops at the first refusal, and marks its events `verb_run`.

  A line that starts with `>` is an attempt, whatever its words. A word nothing answers to is logged to `reaches/<world>.jsonl`, so reaches can be read later without being announced to everyone.
- **Tier 2, commissions and workers** (`notation/workshop.py`; `help commissions`).
  - A task with `commission=asked` is taken by a disposable `claude -p` worker with real tools. It works in its own git worktree (`.worktrees/<id>`, branch `worker/<id>`), on a copy of the world named `<world>-try`.
  - It talks to whoever asked through comments on the task.
  - It says it is done by committing and setting `commission=ready`.
  - The house lands it between passes: `health.py` before and after a `--no-ff` merge, and a revert if health fails or a lens stops compiling.
  - States: asked → working → waiting ↔ working → ready → landing → landed | reverted | failed | cancelled.
  - Alex: commissions are trusted, not granted by him.
- **`notation/health.py`** is what a landing must pass: Python parses, `node --check` on the JS, test_scene, the golden session prints (0 differ), and every lens in the world compiles. About 7 s. `--json` for machines.
- **`notation/keeper.py`** keeps deskd and the house on the current code (F23). It restarts deskd when HEAD moves, restarts the house when it exits 75 (it asked, after a landing changed Python), and reverts a `land ` commit after three house deaths since it landed. A second house on one world refuses (exit 76). The painter reloads when `/api/version` changes, never mid-gesture or mid-typing.
- **`notation/try_worker.py`**: a real commission in a throwaway checkout, landing on a `trial/<tag>` branch (never main), with a report in `trials/worker-<tag>.md`. Two have run (help-list and health-times); both were reviewed and merged.

Running it live on frontier (not yet done; waits on Alex's go): stop any hand-started deskd on the port, then

    C:/Projects/Agora4/.venv/Scripts/python.exe keeper.py frontier --port 8794

from `research/text-desk-lab/notation/`. Its log is `house-state/keeper.log`.
