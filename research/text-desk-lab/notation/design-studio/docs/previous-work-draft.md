# Previous Work

**Draft · 23 September 2026 · Earlier Agora architectures, oldest first**

Agora has been rebuilt several times in four weeks. Each attempt kept the same aim: a person and JEFF share one malleable environment. Each changed what counted as the substrate. This note sketches every generation so its lessons survive after the old documents are archived. Dates come from git commits unless marked otherwise.

Evidence and claims are kept apart. *Built* means code existed. *Evidenced* means a recorded test, live model run or real browser check. The Agora4 vault labels four September 5 documents **prototype lineage**: Personal Lenses, Executable Components, Astra Harness and Security Addendum. They record results from the Milestone One line, not the APIs or guarantees of any later runtime. For what exists now, see [[Current Implementation]].

## 1. The design vault (late August to 2 September)

**Goal.** Describe a whole operating system of persistent objects shared with a resident agent, before writing code.

**Core model.**
- Entities with typed, scoped facets; identity separate from content, location, view and activity.
- Verbs as the only way anything changes; an append-only event log as truth.
- Reconcilers for maintained intent (spec/status pairs), brokers for external effects.
- A host "keep" holding authority outside the agent's reach; claims are not grants.
- A Constitution, rooms, the web and governance as the social horizon.

**Built and evidenced.** Documents only, plus research dossiers dated 31 August: graph memory, an object/facet pressure test with 14 executable toy counterexamples, a whole-OS object revision and scoped-collaboration security models. The toy models passed their own checks; nothing else was run. First commit `f7cdc90` (2 September); reorganised into an Obsidian vault the same day (`5a8468e`).

**Lessons.** The strongest idea is continuity: the same subject survives changes of view, tool and session. The reviews found that a shared reference does not make edits mergeable, a recorded path does not preserve a file, and a discoverable action is not an authorised one.

**Superseded because** prose could not show whether the model was useful. Its mechanisms were later reclassified as hypotheses (the 56-entry review of 9 September).

## 2. The spine, `attempt1` (about 2 to 3 September)

**Goal.** Implement the vault's §22 roadmap directly.

**Core model.** One SQLite log with a hash chain and delete-refusing triggers; ULID identities; a level-triggered reconciler runtime; brokers with receipts; an interim in-world grants table; lenses and a portal.

**Built.** Working modules and tests, never committed. It survives only on disk.

**Superseded because** it carried Milestone Two features before one claim had been tested. It was replaced by a deliberately smaller restart (DECISIONS, 3 September).

## 3. Milestone One and its extensions (3 to 6 September)

**Goal.** Prove the smallest loop: a person and JEFF change one world through one path, and the world rebuilds from its log.

**Core model.**
- A JSONL event log as truth; SQLite derived by replay; blobs by hash.
- Exactly four verbs: `mint`, `attach`, `read`, `place`. JEFF's tools were derived from the verb registry.
- Text as a Loro CRDT; projection at fixed token budgets shared by the shell and JEFF.
- A thin FastAPI shell; JEFF as an ordinary client acting as actor `jeff`.

**Built and evidenced.** Commit `80a43da`: 72 tests and a live acceptance run with claude-haiku-4.5 (import notes by chat, restart, rebuild from the log alone). A 4 September holistic review and a static security review found that file import read the host before authority checks, and that the loopback shell was unauthenticated. On 5 September these were repaired, bringing the suite to 99 tests, and three extensions followed. All three are prototype lineage:
- *Personal Lenses:* a declarative list/detail view stored as data, previewed and then activated at a pinned revision.
- *Executable Components:* JavaScript run in bounded QuickJS processes, with scoped effects, disposable candidate worlds and pinned activation. A real Sonnet 4.5 conversation authored dragging and then an alphabetise action.
- *Astra Harness:* JEFF moved to GPT-6 Astra through the Codex SDK and managed account sign-in. The suite reached 130 tests, and a check against the compiled runtime confirmed which tools the model actually had.

**Lessons.** A refused action must leave no trace. Pin code revisions while data stays live. A scripted program shows the runtime can do something; only a real model trial shows JEFF authored it. Enumerate the real tool inventory rather than trusting configuration.

**Superseded because** Alex required JEFF to invent abilities during use. A fixed vocabulary could not do that, and authoring components inside QuickJS was costly. A 5 September proposal recommended editable application packages with a Linux workspace. Checkpointed as `df9a149` (branch `codex/agora2-checkpoint-20260906`).

## 4. Agora3: native runtime and Linux workspace (6 to 9 September)

**Goal.** Build a fresh native-development runtime, with no imports from earlier code.

**Core model.**
- One authenticated host gateway with a transactional SQLite journal and derived cache. Replay never executes anything.
- Packages with separate source, build and installation identities (`browser-1`, `Python-1`).
- A dedicated VirtualBox Ubuntu guest with broad root access, and a separate resettable candidate VM ("yard") with no live token.
- A narrow RPC bridge from the guest over pinned SSH. Recovery sits outside the authored shell.
- JEFF on the host, with only generic discover and invoke tools.
- The shell itself is an installed native package.

**Built and evidenced.** Commits `87da4f8` to `7be2540`. Tests covered replay, stale-write refusal, authentication, revocation and recovery. Guest probes covered root execution, timeouts and reconnection. Live JEFF authored and invoked a counter package, and later authored note dragging, exercised with real pointer input. After the Markdown chat upgrade the suite had 90 tests. On 9 September a presentation experiment ran 18 real JEFF turns: 1498 s for the baseline against 741 s for the prototype, from one trajectory each. Human testing then found defects that the agent checks had missed.

**Lessons.** Keep recovery outside what is being rewritten. A successful build is not evidence of interaction. The agent path can work while the human controls are broken. Whole-package saves and hand-written DOM plumbing were the main sources of friction.

**Superseded because** it continued directly into Agora4. The same day's documentation compression removed too much rationale.

## 5. Agora4: applications, resident JEFF, parallel work (10 to 17 September)

**Goal.** Restore the full design vault with explicit status labels, and make the runtime a place to live.

**Core model.**
- Independent browser applications. Notes and Documents edit one shared object through separate packages. Each open appearance keeps its own drafts, selection and lease.
- One resident, JEFF0, bound to a single durable model thread. If resuming that thread fails, JEFF0 refuses rather than starting a new identity.
- Parallel work (`codex/parallel-worldline`). Durable tasks run attempts in scoped candidate worlds, two workers at a time, with resource leases. "Ready" does not mean installed: adoption rechecks the current inputs.
- GPT Live voice, with a protected reload of voice code between calls.

**Built and evidenced.** Recorded counts: 145 tests and 28 real Edge checks for the application merge; 185 tests and four live worker rounds for parallel work, with native replay matching 1,406 objects; 190 tests after the 12 September recovery; 201 tests after the live-update repair. A live thread dump confirmed a deadlock between chat steering and history requests, and the fix was regression-tested. A sustained real voice call after the final repair remains unverified.

**Lessons.** Never hold world authority, or a lock, while waiting on another runtime. Flush drafts before replacing a view. Keep Alex's orientation prompt verbatim and separate from runtime guidance, and verify that both reach the first resumed turn. Copying a world does not transfer identity.

**Superseded because** active work moved to the text desk from 16 September. The recorded pressure was per-application JavaScript, heavy machinery for each change (VMs, packages, candidates), and the arrangement findings below. JEFF0's world and the runtime source are retained, not deleted. The last `agora4` commit is `c9ab3d8` (17 September).

## 6. Design labs on the Agora4 line (15 to 17 September)

- **Arrangement lab** asked whether one spoken intent could rearrange forty windows with one receipt and one undo. Seven real JEFF runs showed that a generic placement API with atomic batches is insufficient. What is missing is addressed intent, bounded selection, proposal composition, admission and compensation. The comparison against the current world was withdrawn after a baseline mismatch.
- **Tessera** tested whether three GPT-5.6 builders could compose a working program from unordered JSON claims, with no coordinator merging their code. Incompatible claims block and name both authors. Claims that point at missing definitions go dormant rather than failing. Six trials ran, from a notes workspace to a live particle sandbox. The lab also concluded that set-union convergence does not guarantee semantic correctness.
- **Language interface** proposed a small adapter so JEFF could talk to the environment about its capabilities. Nothing was implemented.
- **First text desk** asked whether a model can do precise desktop work through `look` and `act` without writing code. GPT-5.6 Terra passed most of the hard missions. The runs exposed a real undo defect. One run reached the correct final state through a bad decision.

## 7. The text desk and its sibling labs (16 to 23 September)

The notation lab ran 47 Terra trials (rounds 1 to 9). They produced the line notation, the verb registry, selections, seen-fencing and receipts. Later rounds turned the lab into an inhabited desk with rules, scripts, views and lenses. That desk is the [[Current Implementation]]. On 18 September the separate histories were joined into one `main` (`97c11db`). Two sibling labs remain research only:
- **Design studio** (18 September): four Opus designers converged on a single line grammar and on marking how each fact is known.
- **Shared visual desk** (branch `research/shared-visual-desk`, rounds 1 to 8): Astra research teams compared foundations, built the Clearing and Commonplace desktops, and tested bridge adapters over the lens compiler (58 checks in disposable worlds). None of it is installed. Round 8 asks facets to earn their complexity against document/plugin and live-object alternatives.

## Reusable lessons

| Lesson | Where it was learned |
|---|---|
| One authenticated write path; a refused action leaves no trace | Milestone One, Agora3 |
| Replay restores state and never repeats effects | Design vault, Agora3 |
| Refuse stale writes; record what the actor saw | Milestone One, text desk |
| Pin definition revisions; keep the last good version and recovery outside | Lenses, components, Agora3 shell |
| Candidate ready is not installed; adoption rechecks inputs | Agora3 yard, parallel work |
| Verify the real tool inventory, not mocks | Astra harness |
| Separate mocked, inventory, guest, live-model and human evidence | Agora3, presentation experiment |
| Subject and appearance are distinct; drafts belong to appearances | Applications experiment, text desk |
| Never wait on another runtime while holding a lock | Agora4 recovery |
| Grouped intent needs selection, admission and compensation | Arrangement lab |
| Convergence is not correctness; report conflicting authors | Tessera |
| Compressing documents loses rationale; label status instead | 9 to 10 September docs |

## Where the material lives

| Material | Location |
|---|---|
| Design vault (retired) | `C:/Projects/Agora4/docs/`, duplicate in `C:/Projects/Agora/docs/` |
| Original vault commits | `f7cdc90`, `5a8468e`; branch `master`, tag `pre-weave/master` |
| Spine attempt (uncommitted) | `C:/Projects/Agora/attempt1/` |
| Milestone One and extensions | `codex/agora2-checkpoint-20260906` (`df9a149`); branch `docs`, tags `pre-weave/docs`, `pre-weave/docs-final`; ignored copies in `C:/Projects/Agora/{kernel,jeff,shell,component_runtime}` |
| Their validation reports | `research/holistic-review/` |
| Agora3 | branch `Agora3` (`7be2540`), checkout `C:/Projects/Agora3`, `research/local-snapshots/agora3-build/` |
| Agora4 runtime | branch `agora4` (`c9ab3d8`), merged into `main`; `archive/agora4-before-recovery`, `archive/agora4-docs-restoration`, `experiment/native-applications` |
| Parallel work and WIP | `codex/parallel-worldline`; `codex/wip-*` worktrees under `C:/Users/Alex/.codex/worktrees/` |
| Private worlds (not in git) | `C:/Projects/Agora/worlds/` (`parallel-desk` is JEFF0's live desk) |
| Presentation experiment, authored examples | `C:/Projects/Agora4/experiments/`, `examples/` |
| Labs | `C:/Projects/Agora4/research/` (arrangement, tessera, language-interface, security, graph-memory, reviews) |
| Shared visual desk | branch `research/shared-visual-desk`; rounds 7 and 8 uncommitted |
