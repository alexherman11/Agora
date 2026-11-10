# Proposed doc edits, 3 Nov 2026 (for Alex's yes)

> **Applied 3 Nov on Alex's "Yes, apply all"** (9 meant no edit). In edit 2 the line says "the ten below are an older snapshot (old desk event e35003)" instead of "snapshot as of 3 Nov", because the ten rules listed are the old desk's copy.
>
> Draft by Claude. Each edit is small and targeted, and the surrounding text stays as it is. Say yes or no to each by number.

## AGENTS.md

**1. The intro paragraph.**
- Old: "Right now Agora is a **text desk**: … It lives in `src/text-desk/notation/`. The desk is both the prototype we are building and the place the team lives and works."
- New: "Right now Agora is your **desktop**: the kernel (`src/agora/`), served on 8810 by `src/desktop/kernel-desktop/`, changed through Lines. It is both the prototype we are building and the place the team lives and works. The old text desk (`src/text-desk/notation/`) was archived on 27 Oct; its world is kept read-only at `C:/Projects/Agora/archive/frontier-2026-10/`."

**2. The rules block's first line.**
- Old: "Read the live charter first: `read a6529 :3`. Single source in the world; snapshot as of event e35003."
- New: "Read the live charter first: `look dk838` on the desktop (8810). Single source in the world; snapshot as of 3 Nov."

  The ten rules listed under it stay. The builder prompt currently tells workers to skip this line, so this edit fixes that too.

**3. One line under "Epics, stories, tasks".**
- Add: "Every card has a level (Alex, 3 Nov): 1 easy board commands, done directly; 2 workers working with desk agents; 3 you and an agent working together, which waits for you."

**4. In "Desk hygiene".**
- Old: "Private experiments go in your own world (`<world>-<your name>`) or a fork of the shared one (`worktree fork <name>` in the desk)."
- New: "Private experiments go in a separate desktop world (`kdesk.py --world <dir> --port <n>`), never your live one."

## Current Implementation

**5. A banner at the top only.**
- Add: "> This describes the text desk, which was archived on 27 Oct. The kernel desktop is not written up here yet. Until it is, see `src/agora/SHAPE.md`, `src/agora/guide/HOW-TO-BUILD-HERE.md`, `src/desktop/kernel-desktop/README.md` and `help` in the world."
- **Question:** do you want a kernel section added, written a piece at a time with each piece shown to you first?

## Previous Work

**6. A short section 8 after section 7.**
- Add: "**8. The text desk lived in, and the move to the kernel (23 Sep to 27 Oct).** The desk (`frontier`) became where the team lived: JEFF, residents, a house that landed workers' code, about 100 lenses, adapters, card rules. The kernel was built from 23 Oct as a new kernel with the same language, and took over your desktop. On 27 Oct you moved JEFF, Sable and Pike in and archived the old world whole. On 3 Nov workers began bringing back what you used daily: Twitch, card rules, music and a universal viewer. What came over: `src/agora/OLD-WORLD-AUDIT-20261103.md`."

**7. One row in "Where the material lives".**
- Add: "| The text desk's world (frontier) | `C:/Projects/Agora/archive/frontier-2026-10/` (read-only JSON; README first) |"

## Dynamic Desk and Agora

**8. Dynamic Desk "Rooms": a one-line note above it.**
- Add: "> *3 Nov:* the text desk's rooms, corners and Lounge were abandoned on 27 Oct; shared spaces between people continue in communities."

**9. Agora.md "Rooms": leave it alone?**
- That section is your words about people sharing a desk, which isn't what you abandoned. My suggestion is no edit.
