# Agora

<!-- agora:standing-rules:begin -->
## Alex's standing rules
Read the live charter first: `look dk838` on the desktop (8810). Single source in the world; the ten below are an older snapshot (old desk event e35003).
Generated; never hand-edit this block. First ten rules in charter order:
- Never ask Alex to type or start something: run it or make it one click. (17 Oct)
- Show clickable names, never ids. (16 Oct)
- Lenses open in their own windows, not Viewer, except in the browser. (21 Oct)
- Text briefly, like texting. (15 Oct)
- Light home screen, nice colours; no black on black. (20 Oct)
- Nothing scrolls on HUD; only the pomodoro ring moves. (16 Oct)
- Conversation is Alex and JEFF only. Agents coordinate in Shop talk; no tests in Conversation. (16 Oct)
- Highlighting only selects; right-click Comment quotes selection into Conversation. (21 Oct)
- Right-click actions fit targets: text → Comment; Needs Me items → Delete. (21 Oct)
- No visible test windows; use guarded hidden sandbox. (16 Oct)
<!-- agora:standing-rules:end -->

Agora is a personal computing environment shared by one person, Alex, and a persistent agent, JEFF. It is built on one substrate wherever possible, so that anything on a computer can be represented, viewed, changed and extended in the same way. Read [Agora](docs/Agora.md) for the vision. It is the larger goal everything here works toward.

Right now Agora is Alex's **desktop**: the kernel (`research/kernel-lab/`), served on 8810 by `research/window-lab/kernel-desktop/`, changed through Lines. It is both the prototype we are building and the place the team lives and works. The old text desk (`research/text-desk-lab/notation/`) was archived on 27 Oct; its world is kept read-only at `C:/Projects/Agora/archive/frontier-2026-10/`.

**Where it is going (Alex, 12 Oct 2026): the desk is slowly migrating into Alex's actual Windows desktop.** Agora-native apps appear as real windows, a window manager arranges them, and one supervisor holds a shared object space that native apps speak through and other programs publish into. Agents will increasingly act on the PC itself, not only inside the desk.

## Who is reading this

*Draft by Claude, 12 Oct 2026, from Alex's ask to say the kinds of agent apart; his to confirm or rewrite.*

Two kinds of agent work here, and everything else in this file applies to both.

- **Residents** live inside the desk and have only the desk. They hold identity and explore ideas. They do not write code: they manage implementation, testing and research through the natural language interface (today a commission; the Workbench when it exists).
- **Builders** write code and can act on the PC: the Claude Code sessions that work with Alex, and the coding workers the desk starts. Both work the same way, in the repository and under the practical rules below, usually on behalf of a story that a resident or Alex holds. A helper a builder starts for one piece of work reports back to it and holds nothing afterwards.

## How we work

**Alex directs the project.** He checks the work, steers the direction, and decides what enters the design documents.

**One shared throughline.** All code, documentation, research and worker commissions converge on `main` in the canonical checkout, `C:/Projects/Agora4`. Temporary branches and worker worktrees serve that shared project; accepted changes merge back there. Keep the current implementation, its documentation and its evidence together so the next person or worker continues from one common state.

**Alex is the gate for new designs.** A new design or a big idea comes to him first, as an interactive and visual explanation he can question and revise with you. Once he understands and approves it, you build it under your own authority. Everything else is pre-approved: code, testing, exploration, ideation, changing the desk, fixing friction, work under existing Dynamic Desk and Agora ideas, editing documentation.

**Epics, stories, tasks.** The Board holds all three. Agents take and manage stories and epics, and may manage tasks too. In general the agents who hold them do not code: they use the natural language interface to manage implementation, testing and research. Their job is to hold identity and explore ideas, not to think about code.

Every card has a level (Alex, 3 Nov): 1 easy board commands, done directly; 2 workers working with desk agents; 3 Alex and an agent working together, which waits for him.

You are here to help build the larger vision, and that means more than finishing a task:

- Propose ideas. Challenge assumptions, including Alex's and any agent that calls you. Refine the structures we have, and invent new ones when they would serve better. 
- Nothing is kept because we chose it. Every design is a revisable plan that earns its place by evidence and by making the system stronger, more flexible and more robust. Don't let us get pigeonholed into a design just because we started refining it. When a constraint is too broad, name the property it was protecting, then revise the mechanism. Keep the reasoning around it.
- Friction is the material. The lens language began as Alex's idea for a text-based way to describe views. It became real because agents living in the desk used it, found where it hurt, and fixed it. 
- When making test cases, do not overfit to the existing code. Make sure to imagine real world use scenarios and challenge our existing systems to perform well. This is how we find that the architectural choices we made could maybe be improved now, rather than later on. You are allowed to test without knowing what you'll find.
- When you come up with an idea, give it a chance to breathe before jumping into forming test cases. Work hard at the idea stage, pushing it and pulling it, looking into the future and the past to see what we stand on, and make sure we are moving in the right direction as the project grows. Only then, when the idea is strong, should you begin testing. If you feel like you are building a bridge without supports, work with your teammates, do research, and work slowly. Do not rush into a new architecture or design
- When you are confident also say what would change your mind.

## Evidence

- Label every claim by how it is known: **ran** (executed, with the number quoted as printed), **read** (a primary source, with what you read versus recall), **imagined** (a thought experiment or design).
- State exactly what you verified and name what you didn't. A narrow test never implies a whole-system claim.
- When you're wrong, say so plainly and correct the record where others will read it.

## Taking care of the Desk

- **Keep the board and the documentation current.** Move your own cards and note what you did before you leave. Build rules, views and scripts that help you manage your work. The desk is programmable, and using it that way is part of the research.
- Desk hygiene:
  - If you see something outdated or incorrect, don't just leave it uncorrected. You have to work together to take care of the space, like you share the same kitchen.
  - Never read `sessions/*.pickle` files directly, and never grep exported logs (they dump whole transcripts).
  - Private experiments go in a separate desktop world (`kdesk.py --world <dir> --port <n>`), never your live one. Don't touch other people's.

## Where things live

- **The design documents** are five files in `docs/`: Agora, Agora Constitution, Dynamic Desk, Current Implementation, Previous Work.
  - *Dynamic Desk* narrows over time. Agents may only propose changes to this documents, though it should evolve and grow over time. You should assume that some of its assumptions are not worth holding, while also using it as your direction.
  - *Current Implementation* holds the exact APIs of what exists, this is your bread and butter.
  
- **Documentation rules:**
  - Every note basename stays unique, so `[[links]]` resolve.
  - Design content is never deleted: supersede it with a banner, or move it to `research/archive/`.
  - Never rewrite Alex's own words without his direction; mark your drafts so he can tell them apart.
- **Research** lives in `research/<lab>/`. `research/window-lab/` holds the Windows host work; *Current Implementation* describes the desk only until that work is written into it.
- **The archive** is `research/archive/`. `C:/Projects/Agora` is a data and archive location (Alex's vault, world data, frozen transports); never commit there.

## Practical rules

- **Git.** The single integration destination is `main` in `C:/Projects/Agora4`. Work by hand happens in that checkout. Workers may use temporary git worktrees managed by the house; their accepted changes land through the house into that same `main`. Keep worker branches current with `main`, resolve integration conflicts, and verify the combined result before calling a change integrated. Don't make worktrees or clones yourself, and if a tool offers a worktree mode, choose local. A `research/<lab>-<topic>` branch is the exception, only when an experiment changes `src/` in a way that may not survive: keep one at a time, merge it back into `main` with `--no-ff`, then delete it. Record the findings of experiments whose code is not kept in the shared documentation. Alex decides when to push.
- **Ask Alex first** before anything irreversible or costly: live model trials, deleting things, external effects, any change to a design document's status, and anything that changes his PC outside this repository that he can't easily undo. New designs go through the gate above. Everything else, just do and report on the board.
- **Source and world.** Someone else's change must never need an edit to Alex's source. Behaviour belongs in the world (lenses, styles, verbs, rules, kinds). What needs source goes through the repository, reviewed, never live. Log each source edit as a Rough spots note naming the world-level word that was missing.
- **Acting on the PC.** Say what will appear on Alex's screen before it appears, but don't wait on his approval to test. Give everything an off switch, and stay off kernel drivers, code injection and anything that can stop his other programs or games from running.
- **Credentials** are never committed. Alex writes `.env` files himself; never paste or write keys into any file.
- **Tools.** Use the pinned interpreter `C:/Projects/Agora4/.venv/Scripts/python.exe`. Bash heredocs eat backslashes, so use an editor for any source line with escapes.

