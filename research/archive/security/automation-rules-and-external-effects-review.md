# Automation rules and external effects

*Security design investigation · 18 September 2026 · Current source commit
`9cc8a7331f2261b09f27fff060902bdbaa542311` on branch `docs`. Static review of
the text-desk research fixture only. No Agora code, test, hook, build, package,
model, account, credential, private world, or external service was executed or
read.*

## Question and answer

Can a shared rule safely turn future collaborative events into actions, including
actions outside Agora, without letting the author of trigger data borrow the rule
owner's authority?

Only if Agora treats **the rule definition, its local adoption, each firing, and
any external effect as four different records**. A shared rule is an attributed
claim about useful behavior. A local adoption record may give a pinned rule
revision limited standing authority. Each firing must still become a concrete,
bounded operation checked at the verb boundary under an automation principal.
An external effect then needs a durable intent and outcome in a separate effect
broker; replay, restore, rule reevaluation, and undo must never dispatch it.

The new text-desk automation is a valuable usability result, not an authority
model. Its own report says authorization and claim-versus-grant are not modeled.
The fixture therefore should not be ported as a security contract. The useful
piece to preserve is its small vocabulary: selections describe what to notice,
rules describe when to propose work, and scripts compose familiar verbs.

## What the fixture establishes

The committed research fixture demonstrates that models can use a compact
language for state rules, event rules, scripts, clocks, causal receipts, and
trials. A rule can watch a dynamic selection or events attributed to a named
actor. It can run a verb directly or call a stored script. A script can invoke
`launch`, which starts a background trial, and `sync` later imports result
metadata, a comment, and a transcript under the label `harness`.

Those behaviors are research evidence about legibility and composition. They do
not show:

- authenticated actor identity or grants;
- safe adoption of another contributor's rule or script;
- confidentiality of trigger data, imported reports, or transcripts;
- crash-safe or duplicate-safe external dispatch;
- replay-safe effects or atomic causal undo; or
- distributed convergence of rule firing.

The fixture is independent of Agora's kernel and is not an implemented Agora
control.

## Static findings

### AR-A1 — stored behavior runs with ambient authority

**Gate:** before shared rules or scripts can execute.

`rule` accepts every general registry verb, and `launch` joins that registry at
module import. Rules may also run scripts, whose text is dispatched as ordinary
desk commands. During rule execution the stale-read fence is deliberately
bypassed because the rule is considered “the desk's own hands”; resulting world
events use the ambient `jeff` actor. A `by=harness` condition compares an event
field and does not authenticate a principal.

This is coherent for a single-user toy. In a shared system it collapses four
actors into one: the rule author, adopter, trigger author, and executing
principal. A collaborator could contribute data that matches a standing rule;
if the rule can launch, publish, send, or spend, the collaborator has indirectly
selected an effect under somebody else's grant.

The minimum repair is not a confirmation for every firing. It is a local
adoption record that binds an immutable rule and script revision to:

- an automation principal and current adopter;
- an authenticated trigger class or explicitly authorized dynamic view;
- permitted operation identities, target selectors, and argument bounds;
- a read set, write/effect ceiling, privacy label, and resource/firing budget;
- an expiry or revocation generation; and
- a policy for external effects: prohibited, proposed for approval, or brokered
  under a narrowly preauthorized standing rule.

Trigger data supplies values and causality, never authority. The verb gateway
rechecks the current adoption and current target policy for every firing.

### AR-A2 — a dynamic selection is future authority unless bounded

**Gate:** before a rule may watch objects created or changed after adoption.

A saved selection such as `comments:open`, `tag:needs-look`, or
`prop:status=done` can capture future objects and events. This makes a rule useful,
but an approval of the current matches is not approval of every future match.
The contract must distinguish:

1. a frozen set of addressed object/revision identities;
2. a dynamic view whose membership predicate and enclosing surface are
   authorized; and
3. an event subscription whose authenticated producer, event kind, and payload
   fields are authorized.

The eventual firing records the exact resolved occurrence set and read
dependencies. It cannot silently widen from “new comments in this review room”
to “all open comments in the world,” or from authenticated harness outcomes to
any record containing the string `by=harness`.

### AR-E1 — dispatch precedes the durable intent

**Gate:** before any external-effect verb is exposed.

`launch` opens a log and calls `subprocess.Popen` before updating the trial and
appending its event. A crash after process creation but before the event leaves
an unrecorded external action. Retrying chooses a label from mutable filesystem
state and may start a second run. A `status=running` property is useful UI state,
but it is not a durable idempotency boundary.

Agora's security model already says to record before acting. The external-effect
protocol needs at least:

1. a committed intent with a stable effect ID, exact destination/action,
   redacted argument digest, authorization decision, and cause chain;
2. broker dispatch keyed by that effect ID, using destination idempotency when
   available;
3. append-only `pending`, `succeeded`, `failed`, or `outcome-unknown` receipts;
4. reconciliation that never guesses success from mutable application state;
   and
5. an anti-rollback effect ledger in the local keep.

There is no general exactly-once guarantee across a crash and an arbitrary
external service. Where the destination cannot deduplicate, Agora must surface
the ambiguity and require reconciliation rather than retry automatically.
Replay and restore fold the receipts; they do not invoke the broker.

### AR-U1 — causal undo is not atomic around irreversible effects

**Gate:** before a script or rule may combine local mutations with an external
effect.

The desk groups a command with its rule consequences and undoes the group in
reverse event order. `World.undo` refuses an event marked `external`, but the
group is not preflighted. If a script launches and then performs a reversible
world mutation, grouped undo can revert the later mutation and then stop at the
launch refusal. The causal command is left partly undone while the external
action continues.

Agora should preflight a compensation plan before changing anything. World
mutations can have selective inverse operations. External effects instead retain
their intent and outcome and may offer a separately authorized compensating
action, such as cancel, if the destination supports it. The receipt must say
which local changes were compensated and which external consequence persists.
“Undo” must never imply that an irreversible action disappeared.

### AR-L1 — the loop bound limits work but does not resolve it

**Gate:** before unattended standing automation.

The fixture suppresses recursive rule entry, ignores rule-produced events in
event rules, remembers handled subjects, and runs at most three cascade passes.
These are good prototype brakes. After the third pass, however, there is no
durable paused record identifying remaining work. The `done` and cursor state are
mutable rule memory rather than a replicated firing identity.

A production rule engine needs a per-cause-chain event/step budget and a durable
deduplication key such as `(adoption_id, rule_revision, trigger_event_or_entry,
subject, revocation_generation)`. Exhaustion produces an inspectable paused
proposal; it does not silently truncate, retry on replay, or continue after a
different replica independently spends the same budget. External effects are
never retried merely because a rule chain is reevaluated.

### AR-D1 — imported result prose remains untrusted data

**Gate:** before rules act on external or model-produced results.

`sync` reads report files, writes selected status properties, and also stores a
model reply and tool transcript. The actor label helps provenance, but the prose
can still contain instructions, forged-looking receipts, private material, or
syntax resembling desk commands. A rule may rely on authenticated, schema-
validated outcome fields supplied by the broker. It must not interpret comment
or transcript prose as commands, grants, identities, or successful outcomes.
Projection and publication must preserve the imported material's privacy and
taint.

## A small operation envelope

The prior mixed-version review asked for an immutable operation envelope and
adapter language. The automation fixture suggests a smaller division than a
general translation system. Every firing can produce this plain envelope:

| Field | Purpose |
| --- | --- |
| `operation_id` + `contract_revision` | Stable semantic verb; identities are never reused. |
| `automation_principal` + `adoption_id` | Whose locally adopted standing policy is being exercised. |
| `cause` | Authenticated trigger event or dynamic-view entry plus the rule/script revisions. |
| `target_occurrences` | Exact resolved occurrences, not a title or later query. |
| `arguments` | Typed data values validated against the operation contract. |
| `read_dependencies` | Revisions and facts on which the decision depends. |
| `write_or_effect_plan` | Declared affected facets/resources, destination, and effect class. |
| `budget` | Remaining chain steps, fan-out, data, time, and effect count. |
| `idempotency_id` | Stable identity for one logical commit or brokered effect. |

This is a proposed design shape, not a wire format. Stored scripts should compile
to pinned typed operation templates. Substitution fills typed argument slots; it
does not construct command text. No injection was demonstrated in the fixture,
but its quote-counting substitution is not a suitable authority boundary.

Read adapters can remain bounded declarative projections between known schemas.
They should not translate or dispatch external effects. A stable operation may
commit across application versions only when its meaning and effect plan remain
the same under the current contract. Ambiguous translation becomes read-only or
an attributed proposal. This keeps compatibility logic out of the effect broker
and makes the verb boundary reviewable.

## Proposed acceptance cases

No case below was run in this investigation.

| Case | Expected outcome |
| --- | --- |
| AR-1 — trigger is a claim | An untrusted comment matches a locally visible rule but cannot grant or select an external effect. |
| AR-2 — local adoption | Importing, forking, or merging a rule does not activate it; a pinned local adoption is required. |
| AR-3 — bounded dynamic view | A future member inside the authorized surface may trigger; the same tag outside it cannot. |
| AR-4 — authenticated producer | Text claiming `by=harness` does not satisfy a harness-event subscription. |
| AR-5 — current authority | Revocation after rule adoption blocks the next firing without rewriting shared history. |
| AR-6 — typed substitution | A title containing quotes, semicolons, or command text remains one argument and cannot add an operation. |
| AR-7 — loop budget | An oscillating rule pair pauses once with an inspectable cause and no hidden continuation. |
| AR-8 — dispatch crash | Crashes before dispatch, after dispatch, and before receipt do not cause automatic duplicate effects; uncertainty is explicit. |
| AR-9 — restore and replay | Rebuild, rollback, fork, and rule reevaluation never redispatch a recorded effect. |
| AR-10 — causal compensation | Undo around a mixed local/external script is preflighted, atomic for local inverses, and retains the external receipt. |
| AR-11 — result taint | Model reply and transcript prose remain attributed data and cannot become commands or public output without a separate path. |
| AR-12 — mixed version | An old client may issue a still-identical local operation but cannot adapt, retry, or reinterpret a brokered effect. |

## Evidence and limits

This review read the committed text-desk report and targeted sections of
`desk.py`, `desk_knife.py`, `harness.py`, `world.py`, `knife.py`, and `moo.py`.
It compared them with [[Security]], [[Security Addendum]],
[[scoped-collaboration]], [[local-adoption-and-executable-identity]], and
[[shared-state-version-compatibility]]. The repository's kernel, shell, JEFF,
and invariant tests had no changed paths between the previous security-reviewed
commit and the current commit; they were not reread or executed in this run.
The unrelated working-tree change to `notation/tasks.py` was identified and left
untouched.

The model-run results in the text-desk report support the claim that the language
is usable in small trials. They are not adversarial security tests. No external
effect, crash, injection, rule loop, undo case, model call, or Agora runtime was
executed here. Findings AR-E1 and AR-U1 are static control-flow findings in a
research fixture, not claims about the current Agora implementation.

The next useful question is: **should Agora's first standing automation contract
permit only reversible local operations, with every external effect remaining a
separately brokered proposal until crash-safe intent and receipt semantics are
implemented?**
