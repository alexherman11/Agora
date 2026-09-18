# Round four: adapting the rules to a shared desktop

Status: isolated executable research model, 2026-09-18. Not an installed Agora capability.

Alex asked whether the rules from The clearing could build the kind of desktop Claude's team is now building. We used their Notes / Editor / Together workflow as a pressure test, with three Astra High researchers and an independent coordinating browser review. The two teams retain separate desks; findings pass through studio Mailbox a490.

## Result

The unchanged evaluator supports useful application behavior: shared-subject selection, draft and save transformations, placement, classification, arrangement and window movement. Rules are editable data with attributed writes, and the same installed rule can apply to a subsequently created note. This is a successful transfer of behavior, not evidence that the interpreter alone is a complete application substrate.

The adaptation requires a substantial explicit domain controller. `model.mjs` supplies identity allocation, deletion, action admission, dirty-draft policy, revision guards, event retention, program installation and text projections. `app.mjs` supplies DOM rendering, input delivery, spatial camera, dialogs and network checkpointing. HTML/CSS still supply the vocabulary and visual design. Installing a rule cannot invent a new widget, rich text editor, raster engine or media pipeline.

## Concrete comparison

| Pressure | This adaptation | Claude desktop source read this round |
|---|---|---|
| Same content through Notes and Editor | One identified note object, two projections | Shared subject separate from appearances |
| Same subject in two spatial locations | Unsupported; one x/y per note | Multiple appearances supported by underlying desk |
| Authored layout and tag/color behavior | Executed by frozen JSON rule evaluator | Application JS plus desk verbs and style system |
| New note gets existing rule | Host allocates ID, then runs installed create rule | Native experimental create verb, application rendering |
| Document editing | Plain multiline text, explicit save | Section parsing, local draft, delayed whole-body rewrite |
| Draft after unrelated appearance change | Preserved, but save may refuse because note revision covers placement too | Subject/appearance distinction provides a more useful granularity |
| Change history | Bounded model events, actor labels, explicit retention limit | Desk event API plus Together projections |
| Persistence | Whole model + program checkpoint to one experimental note | Individual desk verbs address world entities per action |
| Author new software inside the desk | Change bounded rules and source data | Neither this test nor app-name parity establishes general software authorship |

Claude's files were actively evolving. These are source observations, not a claim that all of their running browser workflows were reproduced. Independent review records source hashes, counterexamples and exact scope in [review.md](review.md).

## Start and inspect

From C:/Projects/Agora4:

```powershell
python -B research/shared-visual-desk/round4-shell/server.py --port 8772
```

Open http://127.0.0.1:8772/round4-shell/index.html. `Save desk` checkpoints into the separate ignored `.state/shell.pickle`. The prior Clearing on port 8771 and `.state/visual.pickle` is separate. `team_desk.py --desk shell --as reviewer --command "look"` provides text-desk inspection. A checkpoint is not a native per-gesture transaction or a multi-user synchronization protocol. Its JSON includes the current editor draft and view state; it is a single-actor study, not private per-user draft storage.

The server accepts revision-guarded checkpoints and serves an allowlist of prototype assets. It does not expose an arbitrary command endpoint. There is no Agora deployment or guest execution.

## Evidence and limitations

- Frozen evaluator SHA256: `7535FFBD340AB39BA9540C0FF521F676FC7C991513D2084859622E970762F4CE`.
- 41 Node tests: 20 original evaluator checks and 21 adaptation checks.
- 6 independent interpreter probes and 6 independent controller checks. Some passing probes deliberately demonstrate missing guarantees rather than success.
- 11 Python checks, including separate named-store isolation; Python Ruff passes.
- HTTP: API and evaluator return 200; private state and Python source return 404.
- Independent review exposed a local-event rule changing shared note data without history; admission now refuses it before application. Notes text projection also now includes authored color.
- Identity/lifecycle, rich text spans, arbitrary collection operators, event delivery, media timing, multiple appearances, compilation and executable widget installation remain outside the demonstrated rules.
- The interpreter can replace an existing array with a literal. Therefore the gap is safe lifecycle semantics and dynamic collection operations, not an absolute inability to represent structural data.
- A stale-draft refusal preserves text; explicit discard/reopen recovers the editor, but there is no merge/rebase workflow. Whole-note revisions conservatively refuse saves after position/color/tag changes.

See [Foundations](foundations.md), [Editing](editing.md), and [independent review](review.md) for ownership and evidence. Browser observations are recorded below after actual input testing.


## Actual browser observations

Root used the in-app browser at port 8772, with actual input delivery and DOM/AX observations. All observations are local prototype evidence, not a native installation claim.

1. Typed a distinctive Editor draft. Notes retained committed content until Save note; saving updated Notes, Editor identity revision and Activity with `save-shared-subject` provenance.
2. Typed a second distinctive draft, then Arrange. Exact draft survived; Save refused `Subject revision changed from 1 to 2`. The visible As text dialog showed current subject revision, draft base, exact draft and committed body separately.
3. Used **Reopen saved (discard draft)** after that refusal in the final interface. It restored the committed body, current revision and disabled Save. The discarded text was a deliberately disposable test draft.
4. Created `n4` after the program was installed. It received `#NEW` from `classify-created-subject`; Activity disclosed host allocation plus the contributing rule. This was a test session before the final saved seed.
5. Opened Edit rules and changed the arrangement multiplier from 150 to 210. Installed through the UI, then Arrange. Visible text projection reported x = 20, 230, 440, 440 (the latter two show the still-authored 440 clamp). No evaluator or app source was edited for this behavior change. This transient rule-edit test was not retained in the final saved seed.
6. In the final side-by-side layout, ArrowRight moved n2 through `place-note`; an actual pointer drag moved n3 with the captured camera scale and revision guard. Both produced Activity receipts.
7. Save desk returned experimental subject checkpoint `s02:1`. Browser reload restored the shared body, placements and four accepted events. Console error inventory was empty. Python tests separately cover stale checkpoint rejection and named-store isolation.
8. Initial tall-window overview shrank to 57% and wasted horizontal space. Actual screenshot review rejected it; final defaults use three side-by-side windows and approximately 96% fit at the observed 1280x720 browser size. Notes and Editor retain internal scrolling. Narrow-screen comfortable editing remains unverified and is not claimed.

Screenshot retained locally, outside Git: `C:/Users/Alex/.codex/visualizations/2026/09/18/01a0b5fe-d025-7513-bb15-5a9279c2a259/review/round4-commonplace.png`.

A read-only visit to Claude's current port-8780 desktop showed a working shell and dock with zero windows for actor alex; we did not open their apps or modify their content. Their app behavior comparison above remains grounded in source and their attributed reports, not invented browser testing.

The frontend also guards load responses against intervening local edits and labels saves accurately when newer local edits occur during a request. This was source-reviewed, not exercised with a controlled delayed browser response. Independent review records an offline response-order counterexample against the inspected Claude core source separately.

## What to try next

The strongest next slice is one shared subject with two independently movable appearances, then content editing through either appearance while a draft remains open. This directly pressures identity, occurrence-scoped placement and revision granularity. Keep the evaluator fixed initially; expose the smallest required runtime operations and test authored policies against them. A pretty third application is weaker evidence than passing that workflow.

For software authorship, rules need typed operations that can install/version executable capabilities and their renderers, inspect source and results, and preview a candidate before activation. Those are proposed next mechanisms, not implemented here. General media and rich editing will also need domain engines. The useful common foundation is a shared model of objects, operations, projections and evidence; it need not be one tiny language implementing every algorithm.


## Claude's nominated counterexample: mailbox a532

Jeff replied with a stronger workflow: an unsettled Editor draft while another actor tags the subject, a rule moves its card to another surface, and an informal spatial cluster becomes a group. The requested properties are an actor-meaningful stale explanation, one causal undo that leaves the draft alone, unchanged on-screen card position during grouping, and text projections including draft ownership. Jeff reported that their team had only established the position-preservation property that day and part of the stale semantics; this is their attributed report, not our verification.

We executed [claude-workflow.test.mjs](claude-workflow.test.mjs) against the unchanged evaluator and final controller. It confirms a failure boundary, not successful completion of that workflow:

- Another actor's tag changes the note revision. Save refuses and preserves Alex's exact draft.
- The refusal names numeric revisions, not the actor/action cause. Activity separately records the agent's tag.
- Duplicate appearance, move-to-surface, free grouping and causal-chain undo all explicitly refuse as unsupported.
- Editor text labels its unsettled draft and base revision, but the editor model has no draft-owner field or delayed-settle scheduler.
- Since grouping is absent, screen-position preservation through reparenting cannot be tested here.

This adds one externally nominated pressure test to the 64 focused checks above. A passing assertion in this file records the expected limitations; it does not mean the user workflow passed. The missing mechanisms are lifecycle, scheduling, occurrences, causal history and projection coverage. This is evidence against the sufficiency of our current contract, not a proof that a finite instruction vocabulary can never express those mechanisms.

Liaison evidence: initial a490, interim c528, results c533, incoming a532; final response records this explicit boundary back in Claude's mailbox. No unattended polling is installed.
