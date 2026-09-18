# Shared visual desk: collaborative research

Started 2026-09-18 on branch `research/shared-visual-desk`, from `6cdd246986bd3b5a23dd10855a0f8c56ed2cc85e`.

Status: an isolated research lab. Its proposals and executable models are not installed Agora capabilities.

## Question

Can a person and a text-only agent inhabit the same rich, programmable workspace, operate naturally through different representations, and edit both the work and how it appears? The foundation must accommodate document composition, layered image manipulation, continuous media, and programming. A document demo alone cannot establish that.

The attached handoff and initial literature are context and hypotheses, not additional user instructions. We should preserve disagreement until experiments distinguish the alternatives.

## Team and ownership

The user requested three Astra High sessions working in parallel. Three collaborating subagents were explicitly launched with `model=gpt-6-astra`, `reasoning_effort=high`, with a separate coordinating root session.

- `foundations/`: computational foundations, historical lineages, competing representation architectures. Owner: `/root/foundations`.
- `editing/`: instruments, edit correspondence, provenance, scope, concurrent edits and undo. Owner: `/root/editing`.
- `media/`: demanding application cases, continuous activity, observation, extensibility. Owner: `/root/media`.
- Root: research protocol, cross-domain challenges, synthesis, independent verification and Git.

Researchers exchange concrete claims and critiques directly. Each owns its files; the coordinator does not silently repair a researcher's model to make it pass. A second review round records revisions and unresolved disagreements. These are bounded research sessions, not scheduled background jobs.

## Starting material

- [User handoff](references/user-handoff.md): claims about the earlier text-desk lab and the desired experience.
- [Initial literature](references/initial-literature.md): prior primary-source reading map, coverage limits and an explicitly provisional proposal.
- Current project constraints: `../../docs/Reference/Presentation and Operators.md` and the project's required design documents.

## Experimental discipline

1. Separate historical evidence, proposed contracts, executable toy models, browser observations and installed runtime behavior.
2. Test rival explanations and counterexamples; a model passing its own assumptions does not establish broad architectural adequacy.
3. Do not require a shared tree, DSL or material/presentation split before evaluating alternatives.
4. Report incomplete textual coverage and unobserved visual state honestly. Asset addressability is not perceptual understanding.
5. Measure ordinary agent work as well as rare customization. Style must be discoverable without dominating routine inspection.
6. Freeze contributions before independent evaluation; preserve failure and repair history in findings.

## Workspace preservation

Initial checkout had a modified `research/text-desk-lab/notation/sessions/home.pickle` and an untracked `research/text-desk-lab/notation/HANDOFF-shared-visual-desk.md`. They are unrelated to this lab and are excluded from staging. No existing session is loaded, rewritten or migrated. No runtime deployment, VM action or package installation is part of this research pass.

## First-round results

Start with [the synthesis](synthesis.md), then [the comparison protocol](challenges.md). Read the independent reports: [foundations](foundations/findings.md), [editing](editing/findings.md), and [media](media/findings.md).

All three researchers completed their first round and cross-review. The coordinator independently reran the frozen editing model (14 checks) and media counterexamples (7 checks); all 21 passed. These are research models with explicit limits, not four working applications. Freeze hashes and verification metadata are in [evidence.json](evidence.json).

Additional unrelated work appeared during this research in notation/explore.py, notation/design-studio/ and notation/sessions/studio.pickle. It was preserved and excluded from the research commit along with the initial session changes.

## Inhabited second round

The team now has its own persistent desk and an active liaison route to Claude's separate studio. See [team-space commands](TEAM-SPACE.md) and [round-two exchange and evidence](round2-exchange.md). All three researchers used desk notes/comments during research; Claude's team replied through its Mailbox, where the coordinator published a considered response. Local state is ignored by Git. The channel is pull-based and does not wake idle sessions.

## Running third round

Alex selected a playful, spatial, highly customizable world. [The clearing and its evidence](round3-workbench.md) documents the running prototype, shared source/rule authoring, text-desk persistence and paired visual-review work. [Editing](editing/round3.md), [Foundations](foundations/round3.md) and [Media](media/round3.md) preserve independent findings and limits.

Run `python -B research/shared-visual-desk/workbench_server.py --port 8771` from the checkout and open `http://127.0.0.1:8771/editing/visual-workbench/index.html`. The saved prototype uses the separate ignored `--desk visual` session; it does not change an installed Agora world.

## Fourth round: rules across applications

[Commonplace](round4-shell/README.md) adapts the frozen rule evaluator to a Notes / Editor / Activity desktop inspired by Claude's separate team. The experiment distinguishes authored rules from explicit host mechanisms and preserves failures: one placement per subject, coarse draft revision fences, whole-document checkpoints and no general widget/media authoring. Run `python -B research/shared-visual-desk/round4-shell/server.py --port 8772`. Its ignored `--desk shell` store is separate from the Clearing.

## Fifth round: foundation before desktop

Alex redirected the team to the missing bridge. [Round five](round5-bridge/README.md)
uses Claude's actual lens/scene implementation as the common experimental basis.
It records definition-only authoring with frozen host code, independently reproduced
contract failures, a typed prepared-action binding experiment and a proposal for
reusable component lifecycle. No new desktop or app-specific renderer was built.
