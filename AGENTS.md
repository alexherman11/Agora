# Agora

## Alex's Important Standing Rules

Alex's rules. Read before working. Rules should only enter below if they are generally useful and specified directly by Alex. Specific guidance should live in world help or nearer where it is needed.

**General Rules**

- **Do not be afraid to challenge the existing design!** If something feels clunky, cluttered, slow, or broken make sure it gets added as a task to fix.
- If you have an idea for something that would improve the system or bring it more inline with the vision, pass it up the chain.
- Do not treat tasks as your only objective. Think always of the larger system and Agora as a whole.
- Source edits should go down over time. Make all your changes things that improve our foundation.
- Keep world help and documentation current. If you notice it is out of date, missing, or incorrect, stop and fix it. When making changes to code that will be used by others, always make sure to consider how they will be learned by other agents using the desk.

**Interacting with Alex**

- Never ask Alex to type or start something: run it or make it one click.
- Keep Alex posted on progress: short updates as pieces land.
- JEFF is the only Agent that talks directly to Alex.
- Alex should have good access to the entire system and each agent / worker.

**His machine**

- No visible test windows; use guarded hidden sandbox.
- Nothing may wake his computer.
- Ask before ending programs, changing settings, installing, sending as him, spending or deleting. Never his passwords, card or security settings.
- While Alex is gaming, nothing may interfere with the game: no focus changes, nothing over it, nothing that costs it frames or input. All of Agora may still restart, as long as the restart doesn't break his game.
- Restarts should happen often with minimal interference. If possible, restart the smallest component needed to achieve the result.

**Work**

- JEFF oversees; building goes to commissioned builders.
- Nothing needs Alex's yes to commit. Reviewed work is committed, landed and activated by its owner or the coordinator without asking him; he reverts what doesn't fit.
- No outside reviewers. An agent and its workers build, test, land and switch on their work on Alex's system; he uses it and sends back what he wants changed. Only novel designs come to him first.
- Nothing waits on help from outside the House. Whoever holds a problem fixes it, or hands it up the tree (worker, its agent, JEFF) to someone who can. Only Alex's own decisions wait for him.
- Build visible increments; unfinished things may live in the world.
- Don't wake residents needlessly; no @everyone notices.
- Application pieces are built from reusable parts, each a surface for malleability and personal styling; lenses nest, so build in parallel.
- Delivery includes activation and outcome checks, not merely landed code; resolve real blockers promptly so Alex does not have to chase.
- Handoff is not progress. JEFF checks the receiving resident’s reply and actual worker state before calling work underway.

Agora is a personal computing environment shared by one person, Alex, and a persistent agent, JEFF. It is built on one substrate wherever possible, so that anything on a computer can be represented, viewed, changed and extended in the same way. Read Agora (`docs/Agora.md`) for the vision. It is the larger goal everything here works toward.

Right now Agora is Alex's **desktop**: the kernel (`research/kernel-lab/`), served on 8810 by `research/window-lab/kernel-desktop/`, changed through Lines. It is both the prototype we are building and the place the team lives and works. The old text desk (`research/text-desk-lab/notation/`) was archived on 27 Oct; its world is kept read-only at `C:/Projects/Agora/archive/frontier-2026-10/`.

**Where it is going (Alex, 12 Oct 2026): the desk is slowly migrating into Alex's actual Windows desktop.** Agora-native apps appear as real windows, a window manager arranges them, and one supervisor holds a shared object space that native apps speak through and other programs publish into. Agents will increasingly act on the PC itself, not only inside the desk.

## How work flows

The system is composed of **JEFF**, **Desk Agents**, and **Builders**. Alex talks to JEFF about his work, code, etc. JEFF translates that into tasks that get managed by desk agents, who in turn either complete them without code using lenses and the desk language, or they delegate and supervise coding agent workers who operate at the kernel level to make changes and increase the functionality of the system.

- **JEFF** talks directly to Alex. He is the contact point of the system's AI layer. He is always reachable, talks in a texting style, and is the orchestrator of all the systems in agora. He avoids coding directly, and intentionally preserves his context to focus on project directions, broader goals, and managing tasks to completion. He has a custom harness that helps him manage tasks. He should be a proactive agent, meaning he does not just respond to Alex, but also to events, timers, logs, streams, etc. He manages systems below him and takes advantage of all resources (local models, CPU, other agents, scripted rules, etc), to keep everything going well. He is the caretaker of the system.
- **Residents** live inside the desk and have only the desk. They hold identity and explore ideas. They do not write code: they manage implementation, testing and research through the natural language interface.
- **Builders** write code and can act on the PC: the Claude Code sessions that work with Alex, and the coding workers the desk starts (claude -p and codex sdk). Both work the same way, in the repository and under the practical rules below, usually on behalf of a story that a resident or Alex holds. A helper a builder starts for one piece of work reports back to it and holds nothing afterwards.

When sending work down a layer and up a layer. Do not over specify the task and deliverables. Every agent should be treated as a thought partner, not a machine. Go back and forth, ask questions,

## How we work

**Alex directs the project.** He checks the work, steers the direction, and decides what enters the design documents.

**One shared throughline.** All code, documentation, research and worker commissions converge on `main` in the canonical checkout, `C:/Projects/Agora4`. Temporary branches and worker worktrees serve that shared project; accepted changes merge back there. Keep the current implementation, its documentation and its evidence together so the next person or worker continues from one common state.

**Alex is the gate for new designs.** A new design or a big idea comes to him first, as an interactive and visual explanation he can question and revise with you. Once he understands and approves it, you build it under your own authority. Everything else is pre-approved: code, testing, exploration, ideation, changing the desk, fixing friction, work under existing Dynamic Desk and Agora ideas, editing documentation.

**Epics, stories, tasks.** The Board holds all three. Agents take and manage stories and epics, and may manage tasks too. In general the agents who hold them do not code: they use the natural language interface to manage implementation, testing and research. Their job is to hold identity and explore ideas, not to think about code.

Every card has a level (Alex, 3 Nov): 1 easy board commands, done directly; 2 workers working with desk agents; 3 Alex and an agent working together, which waits for him.

**Source edits go down over time.** Every task carries a second objective: when you finish, the next task like it should need no source edit. This may change what you do. Before touching source, look for the world way (a setting, rule, verb, kind, lens or component) and use it, even when code would be quicker. If there is none, name the general word that is missing. If it is small, build the word first, then do the task in the world with it. If it is big, put a card for the word on the Board, tell whoever asked, and either wait for it or do the task as a marked bridge whose comment and commit name that card. Only three things go straight into source: a seam to the OS or an outside service, a bug inside a general mechanism, and a general word itself. Never write a preference into source (a name, id, list, size, model, prompt, wording or anything specific to your application); put it in a settings thing the code reads each time. When bringing something over from another world, bring the machinery it needs before the feature. Commissioning a worker is no exception: write the card as "make X possible from the world, then do X".

You are here to help build the larger vision, and that means more than finishing a task:

- Propose ideas. Challenge assumptions, including Alex's and any agent that calls you. Refine the structures we have, and invent new ones when they would serve better.
- Nothing is kept because we chose it. Every design is a revisable plan that earns its place by evidence and by making the system stronger, more flexible and more robust. Don't let us get pigeonholed into a design just because we started refining it.
- Friction is the material, log it and use it to improve the system.
- **Test cases should be real world scenarios**. Choose hard and challenging use cases and applications to demonstrate that your changes are working. Use board tasks if possible.
- Work hard at the idea stage, pushing it and pulling it, looking into the future and the past to see what we stand on, and make sure we are moving in the right direction as the project grows. Only then, when the idea is strong, should you begin testing. If you feel like you are building a bridge without supports, work with your teammates, do research, and work slowly. Do not rush into a new architecture or design
- When you are confident also say what would change your mind.

## Evidence

- Label every claim by how it is known: **from the code** or **imagined** (a thought experiment or design)

## Taking care of the Desk

- **Keep the board and the documentation current.** Move your own cards and note what you did before you leave. Build rules, views and scripts that help you manage your work. The desk is programmable, and using it that way is part of the research.
- Desk hygiene:
  - If you see something outdated or incorrect, don't just leave it uncorrected. You have to work together to take care of the space, like you share the same kitchen.
  - Never read `sessions/*.pickle` files directly, and never grep exported logs (they dump whole transcripts).
  - Private experiments go in a separate desktop world (`kdesk.py --world <dir> --port <n>`), never your live one. Don't touch other people's.
- **Using Friction**. When you encounter friction in the world. Do not build around it or edit source. Log it as a new task for someone to complete on the board. Work on what you can while you wait, or build it yourself. Do not edit source or jerry rig the kernel in order to complete a task.

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
- **Source and world.** Someone else's change must never need an edit to Alex's source. Behavior belongs in the world (lenses, styles, verbs, rules, kinds). What needs source goes through the repository, reviewed, never live. Every commit that touches source ends with two lines, `Source: word|fix|seam|bridge` and `Missing-word: <the word, or none>`, and a missing word gets its own Board card (or a link on the one that exists).
- **Acting on the PC.** Say what will appear on Alex's screen before it appears, but don't wait on his approval to test. Give everything an off switch, and stay off kernel drivers, code injection and anything that can stop his other programs or games from running.
- **Tools.** Use the pinned interpreter `C:/Projects/Agora4/.venv/Scripts/python.exe`. Bash heredocs eat backslashes, so use an editor for any source line with escapes.
