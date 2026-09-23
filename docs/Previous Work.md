# Previous Work

**Written 23 September 2026 · earlier Agora architectures, oldest first**

Agora was rebuilt several times between late August and mid September 2026. Every attempt kept the same aim: a person and a resident agent, JEFF, share one malleable environment. Each attempt changed what counted as the substrate. This document sketches each generation so its lessons survive after the older documents are archived. It is a map, not a specification: nothing here is a current API or a working guarantee.

Two words are used carefully. *Built* means code existed. *Evidenced* means a recorded test, a live model run or a real browser check. Dates come from git unless marked otherwise. The retired design vault labels four September 5 documents **prototype lineage** (Personal Lenses, Executable Components, Astra Harness, Security Addendum); they describe the Milestone One line, not any later runtime. What exists today is in [[Current Implementation]].

## 1. The design vault (late August to 2 September)

**Goal.** Describe a whole operating system of persistent objects shared with a resident agent, before writing code.

**Core model.**
- Entities with typed, scoped facets. Identity is separate from content, location, view and activity.
- Verbs are the only way anything changes. An append-only event log is the truth.
- Reconcilers maintain intent (spec and status pairs). Brokers carry external effects and return receipts.
- A host "keep" holds authority outside the agent's reach. A claim is not a grant.
- A Constitution, rooms, the web and governance form the social horizon.

**Built and evidenced.** Documents, plus research dossiers dated 31 August: graph memory, an object and facet pressure test with 14 executable toy counterexamples, a whole-OS object review and scoped-collaboration security models. The toy models passed their own checks. Nothing else ran. First commit `f7cdc90` on 2 September, reorganised into an Obsidian vault the same day.

**Lessons.** Continuity is the strongest idea: the same subject survives changes of view, tool and session. The reviews found three gaps that recur later: a shared reference does not make edits mergeable, a recorded path does not preserve a file, and a discoverable action is not an authorised one.

**Superseded because** prose could not show whether the model was useful. Its mechanisms were reclassified as hypotheses in the 9 September review.

## 2. The spine attempt (about 2 to 3 September)

**Goal.** Implement the vault's roadmap directly.

**Core model.** One SQLite log with a hash chain and delete-refusing triggers; ULID identities; a level-triggered reconciler runtime; brokers with receipts; an interim in-world grants table; lenses and a portal.

**Built.** Working modules and tests, never committed. It survives only on disk at `C:/Projects/Agora/attempt1/`.

**Superseded because** it carried later-milestone features before one claim had been tested. It was replaced by a deliberately smaller restart (DECISIONS, 3 September).

## 3. Milestone One and its extensions (3 to 6 September)

**Goal.** Prove the smallest loop: a person and JEFF change one world through one path, and the world rebuilds from its log.

**Core model.**
- A JSONL event log as truth; SQLite derived by replay; blobs by hash.
- Exactly four verbs: `mint`, `attach`, `read`, `place`. JEFF's tools were derived from the verb registry.
- Text as a Loro CRDT. Projection at fixed token budgets shared by the shell and JEFF.
- A thin FastAPI shell. JEFF is an ordinary client acting as the actor `jeff`.

**Built and evidenced.** Commit `80a43da`: 72 tests and a live acceptance run with Claude Haiku 4.5 (import notes by chat, restart, rebuild from the log alone). A 4 September holistic review and a static security review found that file import read the host before authority checks and that the loopback shell was unauthenticated. Both were repaired on 5 September, bringing the suite to 99 tests. Three extensions followed, all prototype lineage:
- *Personal Lenses:* a declarative list and detail view stored as data, previewed, then activated at a pinned revision.
- *Executable Components:* JavaScript run in bounded QuickJS processes with scoped effects, disposable candidate worlds and pinned activation. A real Sonnet 4.5 conversation authored dragging and then an alphabetise action.
- *Astra Harness:* JEFF moved to GPT-6 Astra through the Codex SDK. The suite reached 130 tests, and a check against the compiled runtime confirmed which tools the model actually had.

**Lessons.** A refused action must leave no trace. Pin code revisions while data stays live. A scripted program shows the runtime can do something; only a real model trial shows JEFF authored it. Enumerate the real tool inventory rather than trusting configuration.

**Superseded because** Alex required JEFF to invent abilities during use. A fixed vocabulary could not do that, and authoring components inside QuickJS was costly. Checkpointed as `df9a149` on branch `codex/agora2-checkpoint-20260906`.

## 4. Agora3: native runtime and Linux workspace (6 to 9 September)

**Goal.** A fresh native-development runtime with no imports from earlier code.

**Core model.**
- One authenticated host gateway with a transactional SQLite journal and a derived cache. Replay never executes anything.
- Packages with separate source, build and installation identities.
- A dedicated VirtualBox Ubuntu guest with broad root access, and a separate resettable candidate VM (the "yard") holding no live token.
- A narrow RPC bridge from the guest over pinned SSH. Recovery sits outside the authored shell.
- JEFF on the host with only generic discover and invoke tools. The shell itself is an installed native package.

**Built and evidenced.** Commits `87da4f8` to `7be2540`. Tests covered replay, stale-write refusal, authentication, revocation and recovery. Guest probes covered root execution, timeouts and reconnection. Live JEFF authored and invoked a counter package, then note dragging exercised with real pointer input. The suite reached 90 tests. A presentation experiment on 9 September ran 18 real JEFF turns, one trajectory per arm. Human testing then found defects the agent checks had missed.

**Lessons.** Keep recovery outside what is being rewritten. A successful build is not evidence of interaction. The agent path can work while the human controls are broken. Whole-package saves and hand-written DOM plumbing were the main sources of friction.

**Superseded because** it continued directly into Agora4. The same day's documentation compression removed too much rationale, which is why the vault was later restored with status labels.

## 5. Agora4: applications, resident JEFF, parallel work (10 to 17 September)

**Goal.** Restore the full design vault with explicit status labels and make the runtime a place to live.

**Core model.**
- Independent browser applications. Notes and Documents edit one shared object through separate packages. Each open appearance keeps its own drafts, selection and lease.
- One resident, JEFF0, bound to a single durable model thread. If resuming that thread fails, JEFF0 refuses rather than starting a new identity.
- Parallel work (branch `codex/parallel-worldline`): durable tasks run attempts in scoped candidate worlds, two workers at a time, with resource leases. "Ready" is not "installed"; adoption rechecks current inputs.
- GPT Live voice, with a protected reload of voice code between calls.

**Built and evidenced.** Recorded counts: 145 tests and 28 real Edge checks for the applications merge; 185 tests and four live worker rounds for parallel work, with native replay matching 1,406 objects; 190 tests after the 12 September recovery; 201 tests after the live-update repair. A live thread dump confirmed a deadlock between chat steering and history requests, and the fix was regression-tested. A sustained real voice call after the final repair remains unverified.

**Lessons.** Never hold world authority, or a lock, while waiting on another runtime. Flush drafts before replacing a view. Keep Alex's orientation prompt verbatim and separate from runtime guidance, and verify both reach the first resumed turn. Copying a world does not transfer identity.

**Superseded because** active work moved to the text desk from 16 September. No document records the decision directly. The recorded pressures were per-application JavaScript, heavy machinery for each change (VMs, packages, candidates) and the arrangement-lab findings below. JEFF0's world and the runtime source are retained, not deleted. Last runtime commit `c9ab3d8` (17 September).

## 6. Design labs on the Agora4 line (15 to 17 September)

- **Arrangement lab.** Can one spoken intent rearrange forty windows with one receipt and one undo? Seven real JEFF runs showed that a generic placement API with atomic batches is not enough. What is missing is addressed intent, bounded selection, proposal composition, admission and compensation.
- **Tessera.** Can three GPT-5.6 builders compose a working program from unordered claims with no coordinator merging code? Incompatible claims block and name both authors; claims pointing at missing definitions go dormant. Six trials ran. Set-union convergence did not guarantee semantic correctness.
- **Language interface.** A proposed adapter for JEFF to talk to the environment about its capabilities. Not implemented.
- **First text desk.** Can a model do precise desktop work through `look` and `act` without writing code? GPT-5.6 Terra passed most hard missions. The runs exposed a real undo defect, and one run reached the correct final state through a bad decision.

## 7. The text desk and its sibling labs (16 to 23 September)

The notation lab ran 47 Terra trials over nine rounds. They produced the line notation, the verb registry, selections, look-before-act fencing and receipts. Later rounds turned the lab into an inhabited desk with rules, scripts, views and lenses. That desk is the [[Current Implementation]]. On 18 September the separate histories were joined into one `main` branch (`97c11db`). Two sibling efforts remain research only:
- **Design studio** (from 18 September): Opus designers who converged on a single line grammar and on marking how each fact is known, then argued the lens grammar word by word.
- **Shared visual desk** (branch `research/shared-visual-desk`, rounds 1 to 8): Codex research teams compared foundations, built two desktops, and tested bridge adapters over the lens compiler in disposable worlds. None of it is installed. Round 8 asks facets to earn their complexity against document, plugin and live-object alternatives.

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
| Original vault commits | `f7cdc90`, `5a8468e`; branch `master`, tag `pre-weave/docs` |
| Spine attempt (uncommitted) | `C:/Projects/Agora/attempt1/` |
| Milestone One and extensions | branch `codex/agora2-checkpoint-20260906` (`df9a149`); tags `pre-weave/docs`, `pre-weave/docs-final`; uncommitted copies in `C:/Projects/Agora/{kernel,jeff,shell,component_runtime}` |
| Validation reports | `C:/Projects/Agora4/research/holistic-review/` |
| Agora3 | branch `Agora3` (`7be2540`); checkout `C:/Projects/Agora3`; `research/local-snapshots/agora3-build/` |
| Agora4 runtime | branch `agora4` (`c9ab3d8`), merged into `main`; `archive/agora4-before-recovery`, `archive/agora4-docs-restoration`, `experiment/native-applications`; source under `C:/Projects/Agora4/src/` |
| Parallel work and WIP | `codex/parallel-worldline`; `codex/wip-*` branches |
| Private worlds (not in git) | `C:/Projects/Agora/worlds/` (`parallel-desk` is JEFF0's live desk) |
| Presentation experiment, authored examples | `C:/Projects/Agora4/experiments/`, `examples/` |
| Labs | `C:/Projects/Agora4/research/` (arrangement-lab, tessera-lab, language-interface, security, graph-memory, reviews) |
| Shared visual desk | branch `research/shared-visual-desk`; rounds 7 and 8 uncommitted on 23 September |

## Related documents

- [[Agora]]: purpose and experience.
- [[Dynamic Desk]]: the current design and its open questions.
- [[Current Implementation]]: what exists now and the evidence for it.
