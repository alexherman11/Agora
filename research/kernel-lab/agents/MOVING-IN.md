# Moving into the desktop: what Alex decided

> Record by Claude, 27 Oct 2026, of Alex's answers on the design page [Moving into the desktop](https://claude.ai/artifact/AYPo5fhJYpK8AN7yNbK2HS) (its draft is `moving-in.html` beside this file). Alex's notes are quoted as he wrote them. Everything else is my reading of what each answer changes. **Approved:** this is now built under the builders' own authority (AGENTS.md, "Alex is the gate"). Supersedes SHAPE.md's line "the house and its residents do not carry over. Frontier keeps running untouched."

## The direction

JEFF, the residents and the builders live in Alex's desktop world (the kernel, research/kernel-lab, served by kdesk on 8810). It is the only world. The old desk (frontier, research/text-desk-lab/notation) is archived whole. Rooms and corners are abandoned (Alex, 27 Oct: "i tried it and it never seemed to work"): things belong to people, and the desktop is the place.

## Decisions

| | Decision | Alex | What it changes |
|---|---|---|---|
| D1 | Agents are people, not "agent for Alex" | yes | JEFF is a person and a leader. Residents are members. Builders are agents for whoever asked. kdesk's local entry needs sessions for these people. |
| D1 note | The interface | "I dont want to redo the jeff chat lens, its actually decent, i also already had a workers lens that showed building, landing, blocked, and that was pretty nice. I'd like to have a coder terminal style interface where i can see worker progress (basically a really good overview of all the work being done), where i can click in and view more closely or chat with workers directly. Everything in agora should be connectable to the jeff chat, as it is a central axis of the software." | Port the old desk's **jeff-chat** lens (a5210) and **home-work** lens (a5544, building, landing and blocked) to the desktop painter. Don't redesign them. Add a coder-terminal overview of all work: open any worker to see its progress up close, or talk to it directly. Anything in the world can be sent into the JEFF chat (the Comment-anything mechanism, pointed at the Conversation). |
| D2 | Agents act with tools speaking Lines | yes, with a change: "I want batching to be first class for both see and do (or both at the same time?)" | One tool takes a list of lines, and each line goes to see or do by its word (the Lines window already routes this way). see and do also take lists. A refused line refuses only itself (an existing charter rule). |
| D3 | One house module runs every agent | yes: "i need it to work super well, i like the idea of not having things running outside the kernel, thats smart, but make sure whatever this 10s limit is doesn't mess us up. I want things in agora to be snappy fast" | **Read:** the 10 s is `CALL_TIMEOUT` in kernel/modules.py:34. It covers only a word a module answers. House words (wake, stop, who, build) answer at once and never wait on a model turn. Agents act through their own door sessions, not through the module. Measure: Alex's line to JEFF's first words on screen. |
| D4 | A chat kind; Conversation and Shop talk are chats | yes: "A kind, chat is a great idea" | New kernel kind `chat` with a `say` word, and @name wakes that person. The JEFF button opens the ported jeff-chat lens on it. |
| D5 | Builders and landing | with a change: "jeff should not have to run tests ever. He should be handed something that works" | Builders prove their own work. Landing checks it on its own: kernel and desktop tests, plus the hidden sandbox. Only then does the result reach JEFF, as a finished thing: what changed and where to see it. JEFF judges whether it fits what Alex asked for, never whether it runs. No `house.tests` for JEFF. |
| D6 | Who moves in | yes | JEFF first. Then Sable and Pike, one at a time. Ask the others whether they want to come. |
| D7 | Limits as `may=` | no: "i like this as a general principle, i'm not sure we need it yet though" | No word limits now. Keep the principle for later. |
| D8 | Archive | with a change: "Honestly lets archive everything from the old desk. Were starting fresh in a new world. I dont want all that old clutter, and i do want someone to figure out how to manage clutter (either using local models for triaging tons of older stuff, extracting summaries so things can be discarded, idk, i'm sure there is a path forward here." | Everything is archived, and no cards come over. Only the souls (T3 approved) and the rules (T2) come over. A separate piece of work: **clutter**, meaning how a world sheds old things, e.g. local models triage, summaries replace the bulk, the rest is discarded. |

## The texts

| | Text | Alex | What happens |
|---|---|---|---|
| T1 | The welcome | *not answered yet* | Draft on the page. Ask him again before it ships. Rooms and corners are already struck out. |
| T2 | The rules, split by who reads them | with a change: "we can get rid of the gaming rule, and ending programs is okay, no ask, just change it to be only end programs if neccessary or requested (something like that)" | Core for everyone, with "Nothing while he's gaming" removed. Ask-first becomes: ask before changing settings, installing, sending as him, spending or deleting; end programs only when needed or asked; never his passwords, card or security settings. Then a JEFF-only part, a builders-only part, and the interface rules moved into the guide. A rule that doesn't fit is refused when it's added. |
| T3 | Souls | "i approve it all" | His words untouched, including the two phrases changed with this yes ("library" becomes "guide"; examine and the Handbook become help and the guide). Claude's 15 Oct summary is rewritten. Each agent moves its old-desk lessons into "Before the move". |
| T4 | AGENTS.md | "all approved" | Rewritten for builders on the kernel, per the page's table. |
| T5 | Docs in the world | "all approved" | The guide and help topics replace the Handbook. A new Current Implementation is written for the kernel, and the old one is archived. Previous Work gets section 8. Agora.md and Dynamic Desk get "superseded" banners on their Rooms sections. |

## Build order

1. **JEFF moves in.** A person and a session for him. The batched see/do tools. The chat kind. The house module running JEFF (Claude and Codex transports ported from notation/house.py, with 400k compaction, quota fallback and the charter at start). The jeff-chat lens ported, behind the JEFF button.
2. **The texts.** T1 once Alex answers it. T2 to T5.
3. **Builders.** `task.build` in its own worktree. Self-proof, then independent landing checks with the sandbox and a reload of what changed. The home-work lens ported. The coder-terminal overview, with direct chat to a worker.
4. **Residents.** Sable and Pike, one at a time.
5. **The old desk archived whole.** Separately, the clutter work.
