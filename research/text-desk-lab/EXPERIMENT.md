# Text desk experiment — 2026-09-16

Alex explicitly authorized iterative interface design in this simulator, including
trying alternatives and correcting the design after observing GPT-5.6 Terra.
This is a new synthetic text-interface experiment, not an implementation or
benchmark of installed Agora, and never opens a live world or VM.

## Question

Can an agent navigate a bounded text projection of a visual environment and make
precise, complex changes through existing, discoverable behaviors, without coding?
Which failures arise from the projection, operation vocabulary, or model decisions?

Start with one typed simulator and two tools: `look` and `act`. Content and visual
containment remain distinct; repeated appearances refer to shared content. Tool
arguments are structured, but perception is a readable outline. The simulator
supplies reusable placement and tiling, exact text edits, references, insertion,
and task-column semantics. No shell/browser/file/code-authoring capability reaches
the trial model. Runtime transport helpers, if present, must be audited separately.

## Fixed initial tasks

1. Meeting prep: distinguish two similarly titled notes, edit one paragraph, add
   a checklist, create shared references, and rearrange only selected appearances.
2. Proposal revision: change only the specified repeated date, insert a section,
   reference that exact paragraph elsewhere, remove one stale appearance, and
   recover from a concurrent content edit without overwriting it.
3. Release triage: inspect evidence, complete only tasks whose dependencies permit
   it, preserve blocked work, add a follow-up task, and distinguish geometric
   movement from a status-changing column move.

Every task has predeclared state assertions and preservation checks. Freeze each
run's prompts, source hashes, starting/final states, model identity, tool calls,
errors and timing. Use fresh model sessions and matched fixtures per variation.
Keep unsuccessful runs; never silently substitute a model. Separate transport
failures, simulator bugs and interface friction. Do not teach a task's solution
in the model instructions or change its checker to accommodate a failed attempt.

Start with a reasonable structural outline. Choose subsequent variations only
after reviewing actual traces. Where practical, rerun a second fresh trial to
distinguish a promising change from one lucky attempt. Reserve a new transfer task
for later testing. This is exploratory evidence, not a statistical model ranking.

## Limits

The simulator assumes authenticated single-user access; it does not prove grants,
browser geometry, production durability, general application adapters, or visual
usability. A common text vocabulary can suggest a future design language, but does
not prove every application should share one storage representation or renderer.
