# The command center

Started 2026-09-28 at Alex's direction. The first home application: a place inside Agora where Alex lives and works with a small team of resident agents, built entirely from Agora's primitives and restylable from inside Agora. The build is also the way Agora improves: when it hits friction, we stop, fix Agora properly, record it in [FRICTION.md](FRICTION.md), and go on. No stopgaps.

Builder: Claude (the teaching session), from outside at first; the residents are meant to take it over from inside.

## Decisions (Alex, 28 Sep)

- **Three new residents.** No coordinator; the old team (Sable, Pike, Juniper, Jeff) is paused and not migrated. Alex is the leader; residents may message him, and each may lead its own disposable workers (later).
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
- `research/command-center/FRICTION.md`: every place the build pushed back, and what was done about it.
