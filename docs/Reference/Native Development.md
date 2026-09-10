# Native development

The goal is software that becomes more useful while someone is using it. JEFF
should be able to build a small editor, browser, research workspace or conversation
interface, then improve it without repeatedly reconstructing the surrounding
shell. A capable default environment comes first; customization is an opportunity,
not a prerequisite for ordinary work.

## Existing structure

The protected service owns native state, package receipts, current authority,
account transport and independent recovery. The Linux workspace supplies general
development execution. Authored shell code runs in a constrained browser frame;
installed Python actions run in the guest. A distinct resettable yard tests
candidates without the live native bridge. See [[Runtime Guide]] for exact
operations and [[Security]] for the authority boundary.

Source, build and installation are distinct retained identities. Editing source
does not activate it. Installation chooses a retained build; restoring application
code does not rewind note data. Native replay reconstructs records without
repeating model calls, I/O or jobs. VM snapshots, native history and external
resources have different recovery semantics.

## Develop through ordinary requests

Discover relevant existing capabilities, use them when they fit, and author a
new one when they do not. Search can be brief and bounded. Routine changes under
the person's existing authorization do not need another ladder of approvals.
Executable adoption retains source/build/install evidence; style parameters and
ordinary data edits can take a cheaper native path.

Test what changed at a scope appropriate to its effects. An isolated experiment
can have a smaller contract than a stable shared package. Relevant failures and
unsupported behavior remain visible. A build receipt alone is not browser or
interaction evidence. Preserve text, draft, focus, selection and usable direct
controls while changing an interface.

Tests for invention start without the relevant tool. Tests for reuse start with
it installed. Incremental-development tests preserve earlier work. These answer
different questions; repeatedly rebuilding a tool is not a demonstration of
successful bootstrapping. Evaluate smaller-agent use separately rather than
inferring it from a successful large-model run.

## Machinery worth improving

Current friction is concrete, and each item is a candidate improvement rather
than a mandate for an unknown future:

| Current mechanism | Useful direction to test |
|---|---|
| Whole-package `package.save` | Revision-aware file reads, search and surgical edits; fewer repeated source bytes. |
| Self-contained HTML browser entry | Retained assets, modules or component reuse when an application needs them. |
| Python action and browser execution paths | Shared contracts/evaluators where useful, without a universal runtime requirement. |
| Actions snapshot at most 1,000 world objects | Declared scoped inputs and relevant dependency guards. |
| Object-level stale-write checks | Targeted or finer conflict scopes when content and presentation contend. |
| Polling and paginated queries | Bounded invalidation or subscriptions justified by actual use. |
| Appearance attached to note subjects | Adapters and independent uses with an explicit compatibility path. |
| Correct native actions but fragile human plumbing | Shared registry adapters and rendered-state inspection; test actual human controls. |

Stable named surface parts and reusable native UI clients could reduce repeated
DOM work. Preview should expose real effective values, not merely validate data.
Renderer attachment and versioning could reduce the duplicated evaluator updates
seen in the presentation experiment. These directions leave executable packages
available for behavior beyond the current declarations.

## Conversations, memory and ongoing work

Talk with JEFF about what was difficult, which tools it trusted, what it had to
rediscover and what would reduce the next edit. Its account is evidence about
its experience, not a substitute for external measurement. Preserve that exchange
alongside tasks, traces, corrections and observed outcomes.

Durable tasks, progress, cancellation and reconnection are useful directions.
The current runtime has one foreground JEFF turn; stopping it does not undo
earlier work or kill every independent guest process. Background workers may be
stateful, temporary, deterministic or model-driven. Choose topology by measured
responsiveness and cost rather than declaring all workers ephemeral.

Explicit memory and work collections can be ordinary packages and records.
Retaining a failed route or a rollback's reason can prevent repeated mistakes;
it does not require an irreversible store of every private payload. Retrieval,
attention and visual prominence need not share one score.

## Comparative development

Start a candidate from the current accepted baseline, compare both on the same
application task, and carry forward the better verified result. Independent
replicas help reveal model variation. Record correctness before speed, complete
versus partial outcomes, model/tool time, source traffic, failures and repair
effort. Keep implementation preparation separate from timed use.

Freeze task and check definitions before execution. Escalate realistic workflows
as the application grows: editing, linked sources, integrations, comments,
conflicting changes, export and background activity. Include requests beyond a
candidate's prepared vocabulary. A small sample improves evidence but does not
establish statistical significance. Honest ties and rejected candidates are useful.

Keep human and agent checks distinct. The presentation experiment's agent paths
passed while its human dialog and text selection initially failed. Record repairs
after comparison separately; do not rewrite measured history to favor a candidate.
If the harness fails, recover the same live run where possible and identify any
discarded attempt explicitly.

## Adoption and portability

Pinned, offered and automatically adopted compatible updates can all express
owner-selected policy. Version changes, migrations, presentation inheritance and
authority expansion have different meanings. Current standing authority governs
resumption after restoration; historical records cannot restore revoked power.

Native export, guest dependency recipes and external-resource availability need
separate evidence. Do not promise whole-machine reproducibility from a source
digest, or require a distributed world before a local application can be pleasant.
