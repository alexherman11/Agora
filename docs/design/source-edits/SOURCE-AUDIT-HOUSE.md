# Source audit: the House module (26 Oct – 4 Nov 2026)

*Evidence for [[SOURCE-EDITS-AUDIT]]. Written by a read-only helper Claude started on 4 Nov; kept as it reported, lightly
trimmed. Labels: **read** (diff or file read), **ran** (executed), **imagined** (judgement).*

Scope: 49 commits from `git log --no-merges --since=2026-10-26 -- research/kernel-lab/modules/house research/codex-residents
research/kernel-lab/agents` plus `--grep=House`, and 3 House-caused commits outside it (2297083f1, 13db35c94, 628209e33).
Every diff read (large ones by hunk); HEAD house.py, builders.py, transport.py read in full. Ran: `look dk1489`, `look dk1813`.
"Logged" means logged in repo docs; the world's own Rough spots were not checked.

Classes: U universal · G fix in a general mechanism · B bespoke · P preference in source · C world content as source ·
S OS/host seam · T test/doc. (w) = written by a House worker.

| commit | what | class | avoidable | how / note |
|---|---|---|---|---|
| ea8f66a54 | old-desk house: compact_at 400k from the house note; nested claude.exe | P→world, S | no | Already world. Kernel port applies it to residents only: workers get a hard-coded 400k (builders.py:375, transport.py:56) |
| 397a55b5c | House module, chat kind and `say`, MCP batching; kdesk `moving_in` writes JEFF, Conversation, Shop talk, house-agent with model literals; jeff-chat lens and style as repo files | U+B/P+C | partly | An agent-invite word plus install-from-Lines. Logged in STEP1-JEFF.md (5 words named) |
| 102c30f8e | `say acts=`; activity.jsonl; kdesk makes a "team" group led by JEFF | U+B | partly | The team is one `make kind=group` line. Not logged |
| 6d64c084e | house.who rows carry colours; `house.doing` | U+B | partly | Colour belongs to the lens; doing should be a live aspect. Not logged |
| 483396e27 | `house.log` built in Python in the console component's format | B+G | partly | A lens join over said lines + activity, if activity were in the world. Not logged |
| fe564da9f | builders.py lifecycle; brief carries a verbatim chat transcript; capacity=2, CHECKS, model literals | U/S+C/P | partly | Engine is source; brief, checks and models belong in settings. Logged (BUILDERS.md `task.build`) |
| e1b47a34b | Codex runtime receipts; `house.retry`; release on claim change | S+G | no | |
| 8f7f89bcf | Codex turn_started, duplicate-text filter, async retry | S+G | no | |
| 855fd7834 | House commits the sandboxed worker's files at review | S+C | no | Codex sandbox cannot write .git. Logged |
| 73454eb30 / 9afefea5e | git without auto-gc; one git at a time; kill tree on timeout | S/G | no | |
| 7dc2144a5 (w) | kernel task.next/revise/review/verify/followup; `rows nextsteps:` special case in kernel `rows` (words.py:937) | U+B | partly | A saved-reading thing and a "wake when a reading changes" subscription. Not logged |
| 87228f07c, 5f3926497, 8e574bcbd | which phases may review again or start a fresh run | G/P | partly | A phase table (M4). Not logged |
| 2b941bd7f | three-way-merge landing around someone's uncommitted edits | S | no | Root cause is process: hand edits in the checkout the House lands into |
| fc9f21bfe (w), 458a7c36b (w) | move_resident.py "Sable only", then "Sable and Pike"; `--resident-manifest`; `wake_policy=addressed` | B (+U) | yes | Agent-invite + install (M3). Logged in SABLE-MOVE.md |
| 62d15b913, 7c5cd5398, d32182598 | busy-file retry, stale-write retry, abort a conflicted review merge | G | no | |
| 4c259b5d4 | Rowan: manager.py (local JSON, exactly 3 tasks), `house.manage`, sessions, `--manager-manifest` | B/P | yes | Superseded ~7 h later by 8a8aa6a02; 13 `manager` branches still in builders.py |
| a34a3e4e7 | Codex resident tool discovery | S | no | |
| 39f996a3b (House part) | one turn per chat; agents read through their own door; `needs=` shapes on house words | G+U | no | `needs=` moved kind checks into the world (good). Left dead `context()` |
| 8a8aa6a02 (+2297083f1) | residents run workers; pools; PROVIDERS, MAX_TURNS, tool lists; brief rewrite; `may` stewards→members with the real gate moved into Python | U+P+C | partly | Settings + brief thing (M2) and M3. Not logged |
| 26cf7ecad | `house.work`, wake receipts; brief tells workers to skip AGENTS.md's a6529 line | G+C | partly | Fix AGENTS.md instead of patching around it. Not logged |
| a24b48f4b → df4d54461 | read worker-chat replies via the owner's session (does not work), then change the wake text to "answer with house.tell" | G, then C/P | partly/yes | Let a module hear the chats it made (M5); notice templates in the world |
| d506dc466 | stewards act on any worker (`steward()` re-scans places in Python); `house.restart` | P+S | partly | Authority through kernel `may` on a worker thing (M1) |
| e14f1fd21 | children never inherit AGORA_KEEPER | S/G | no | |
| f42f59c94 (w), 7ad513d55 (w) | work_overview.py: lane/status sets, sorting, regex parsing of the House's own worker names, ids→names | B+C | partly/yes | Lens filters and grouping over cards + a worker-run live aspect |
| 388d401f9 (w) | `may_tell` tiers owner/lead/Alex/steward | P+U | partly | `may: owner or lead or leaders` on the worker thing |
| 21c80d032 | late events from a replaced process ignored; `kill_tree` | G+S | no | Logged: "process as a world-readable thing" |
| 6fb48a6a8 | reminders, wakes, route to JEFF, `house.hand`, `house.snap`, `guide=<thing>` | U+P/C+S | partly | `guide=` is the model fix; ~6 wake templates and escalation stayed in source |
| d67bd44e0 | snap.py; `hand()` tries sessions until one may set the card | S+B | partly | Kernel `lead` may (built afterwards); loop never removed |
| fbf90fb85 (w, dk1813) | world rules file (good) plus kernel `task.signal` with modes, events, `"JEFF"`, `"curing"` (card_signals.py:11,13,35,52) and ~110 lines in the House | C+B | mostly yes | The card said "add a word only if a rule cannot say it". A rule step that can notify `to= about=` (M5). Not logged |
| 248abac49 | drop queued words when the card moved on; one failure wakes nobody twice | G | no | |
| 5435eeaa6 | brief: `look dk838` instead of a6529 | P/C | yes | Charter id from settings, as residents already have `charter=` |
| b3b3c2e3b | `say about=` may name what the same act made | U+B | partly | Reads `about` with the House's wider sight, against the 28 Oct own-door rule |
| 1502a9a67 (w) | WORKERS.md guide in the repo, which residents cannot read | C | yes | `guide=<thing>`, built 6 days later |

**Tally (read):** 42 source-touching commits. Avoidable: yes 8, partly 18, no 16. Only 7 named a missing world word; none of
those words has been built since. The agent-invite word was named three times (STEP1-JEFF, SABLE-MOVE, ROWAN) while three
bespoke movers shipped.

## Hotspots (read; `git log -L` windows)
builders.py: created 27 Oct, 26 commits in 8 days. `start()` 6 (phases, owner exception, manager branch), `tell()` 5 (who
may tell), `prompt()` 6 (brief text, world ids), wake/outcome texts 4–5 each. house.py 21 commits: `call()` 9, `OFFER` 11.
kdesk.py 7 House-related. Recurring reasons: who-may rules in Python; wake and brief text naming JEFF, Shop talk and Alex;
phase-set edits; per-agent provisioning; views over worker state the world cannot see.

## Preferences hard-coded at HEAD (read, file:line)
- builders.py:99-102 models; 103 MAX_TURNS=25; 104-107 tool lists; 48-51 review CHECKS; 121-124 pool 4; 145 capacity (dead)
- builders.py:24-28,47 phase sets; 268 `'JEFF'` exempt; 447-454 `steward()`; 466-472 `alex()`; 474-489 tell tiers; 499-503 `'JEFF'`
- builders.py:528, 585-596, 636-640, 660-663, 737-744, 772-788 wake/notice templates naming JEFF, Shop talk, Alex
- builders.py:940, 951, 960, 752, 370, 1101, 210, 225, 1183 caps and timeouts; 375 workers' compaction at 400k
- builders.py:1004-1020 the brief (`look dk838`, 8810); 1059 commit exclusions
- house.py:45/52 imports `quota_policy` from the archived text-desk-lab path; 583-606 charter header and welcome; 1047-1101 help
  ("four Claude and four Codex", "Only Alex, JEFF…")
- manager.py:25 exactly three tasks; work_overview.py:4-9, 37-40; kernel card_signals.py:11,13,35,52; words.py:937
- kdesk.py:56-57, 192-241 (moving_in), 289-313 (Rowan sessions), 489-501; move_resident.py; new_manager.py
- Dead code: `House.context`, `House.in_chat`, `Builders.capacity`

## Missing mechanisms (imagined design; counts read)
- **M1 Worker runs and agent processes as world things** (durable facts + a live aspect: phase, doing, process), so `may`,
  lenses and rules apply. ~10 commits. Named on 27 Oct in STEP1-JEFF ("a live aspect any module may supply").
- **M2 house-settings + brief and notice templates read at each use** (models, max_turns, caps, checks, timeouts, tools,
  escalate_to, charter). ~8. `compact_at` and pool sizes already prove the pattern.
- **M3 Agent onboarding word** (invite an agent person; soul/charter/house-agent by ordinary `make` from a reviewed install). 7.
- **M4 One phase table** (accepted words, terminal/resumable, who is woken) as data. 5 + 2 partly.
- **M5 Addressed notices outside chats** (`notify to= about=` usable by rule steps; module hears the chats it made). 4.
- Smaller: a saved reading as a world thing; the painter turning ids into names in general.

## What stays source (read + judgement)
transport.py (spawning, stream parsing, kill_tree, env isolation), git work (worktrees, commit for the sandbox, gc, retries),
snap.py, Codex adapters and receipts, MCP image blocks, `house.restart`, the safety invariants (never replay an uncertain
turn, `saw=` fences, one turn per chat, own-door reading, at-least-once cursor, failure dedupe). About 16 of 42 commits.

## Edits that made it less extensible
Rowan's parallel authority path left in; authority duplicated in Python behind words declared `may: members` (so `help`
misstates it and `word-set may=` cannot change it); `hand()` borrowing sessions; `task.signal` naming JEFF in the kernel;
`rows nextsteps:`; regex over names the House made up; house.py depending on archived old-desk code; House-landed worker
commits carry only a truncated title, so history cannot be audited from the log.

## The helper's thinking (imagined)
The House keeps its state outside the world (builders/*/state.json, activity.jsonl, live.json), so none of the kernel's
general tools can reach workers, and every policy, view and notice about them has to be Python. Asks arrive with people's
names in them and are written in literally. Missing words get named but nothing queues them. The loop is built in an evening,
live that night, fixed live by the same session. Even an explicit brief ("only if a rule cannot say it", dk1813) was not
enforced: the House's review runs tests, and nothing asks whether a diff belongs in source.
