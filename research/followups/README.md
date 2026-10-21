# Durable actionable follow-ups — SOURCE REVIEW ONLY

**Deployment blocked. No live runtime integration, activation, restart or wakes.**

The executable engine is `../text-desk-lab/notation/followups.py`.
`staging.py` + `integration.json` hold exact, hash-checked additive source hunks
for `house.py` and `desk.py`. The current files remain byte-for-byte unchanged.
No existing production file imports the engine. The house's `HOUSE_FILES` set
does not include any file changed here. Landing these inert files cannot wire
this mechanism or request a house restart. Tests compile the staged whole files
in memory; they never install them.

## Causal audit (read, 21 October)

| Incident | Evidence | What it establishes / does not |
|---|---|---|
| Selection/menu quota delay | Commission explicitly identifies the notice as received; task history has queued usage event e18450 and JEFF's paused/new-continuation decision e18570. | Follow-through gap as reported; not a demonstrated lost wake. Did not inspect resident transcripts or assume a subscription failure. |
| Public image delivery landed under lifecycle hold | c8250/e17907 required a deployment block; c8310/e18171 reports landed 9fc86fb, with routing knock e18211. `Workshop.land` has no deployment-hold test, and `landed` requests restart on `HOUSE_FILES`. | A comment/prop hold is not an executable landing gate. Did not query running processes or establish whether a restart actually occurred. |
| Outside session handoffs | `listeners.py` distinguishes unavailable/unknown/handed-on, publishes at most 200 event ids while its process remains, and does not replay calls originally recorded unavailable. Shop talk's preserved browser handoffs ask for ownership; a queued call is not recipient acknowledgment. | Delivery and acknowledgment are separate; no claim that a silent recipient missed anything. No durable historical listener receipt available from this code. |
| Browser acceptance capability | c8402/e18495 asks JEFF to route remaining tests after a failed lane; knock e18496 says “Jeff: woken.” c8401 explicitly preserves partial results and the failure boundary. | Wake routing occurred; a receipt does not perform the capability handoff. No transcript-based model-turn or recipient-ack claim. |
| Alex's originating request | e18595 has knock e18596 “Jeff: woken.” | Event-to-routing evidence only. |

Existing `House.news` persists cursor/inbox/held calls. `Resident.send` persists
pending state before a pipe write and labels successful flush “delivered.”
That label attests the transport write, not model receipt, acknowledgment or
task completion. Existing knock records attest a routing decision, not the
subsequent write. This patch introduces neither retroactive delivery claims
nor a conclusion from silence.

## Small typed contract

JEFF/Alex attaches an obligation to an existing subject with the staged native
Desk command. JSON is one quoted Desk argument, using ordinary Desk quoting:

```text
followups attach <task> '<JSON>'
followups ack <task> '{"receipt":"<receipt identity>"}'
followups pending
followups receipts
```

Attach JSON has exactly these fields:

```json
{
  "key": "review-one",
  "revision": 7,
  "recipient": "jeff",
  "next_action": "Review the landed delivery and record the remaining blocker.",
  "source": "e123",
  "awake_seconds": 600,
  "when": [
    {"field":"landed","values":[],"kind":"delivery"},
    {"field":"delivery_state","values":["blocked"],"kind":"blocker"},
    {"field":"usage_state","values":[],"kind":"quota"},
    {"field":"admission_state","values":["refused"],"kind":"admission"},
    {"field":"capability_state","values":["available"],"kind":"capability"}
  ]
}
```

These are illustrative task revision/event values, not live commands to run.
The supported fields are explicitly bounded in `FIELDS`; predicates are ORed,
empty `values` matches any actual change of that property. There is no Python,
shell, arbitrary expression, provider-selection policy or interpretation of
free-form comments. Completion uses e.g. commission=landed/failed. A delivery
obligation can watch landed, independently of source acceptance or task status.
JEFF owns the next action and the meaning of task state; this engine neither
sets commission state nor changes grants, retries or subscriptions.

The convenience command validates the observed subject revision and delegates
to **ordinary `cmd_do("prop", ...)`**, with the normal actor, seen/fence,
permission and mutation serialization path. It persists a `followup_request`
on the existing task; the journal consumes exact property events, not the
latest prop alone, so multiple obligations coexist. The event's actual undo
snapshot validates the pre-write subject revision even if more task events
arrived before the house pass. Only direct JEFF/Alex acts count; rule/verb
derived requests refuse. These are ordinary world identities, NOT a new
authentication or host authority boundary. This feature grants no host powers.

The same key and same spec are idempotent; a changed spec needs a new key.
Acknowledgments use normal property acts, verified against the exact
receipt's named recipient. A per-command nonce prevents another actor's
refused acknowledgment from making the recipient's actual acknowledgment a
property no-op. It is not a bearer credential.

## Delivery and timing

- One parent-owned atomic JSON journal, under the existing world's house-state
  directory; one writer is the existing serialized house loop. Desk only reads
  the fixed path for its own session. No new port/service.
- Exact source event, attach event, title, observed task state, old/new material
  values, next action and awake-time fact timestamps survive restart.
- Current task state is refreshed from the world, including undo/removal.
  Historical receipt facts remain historical; they do not assert that the
  recorded transition is still the task's current state.
- Busy recipients queue. Deliberate resident rest can end for this explicit
  actionable call; want=rest/offline recipients stay pending. No process is
  started by this engine.
- Queued batches coalesce all facts. Superseded queue receipts remain linked.
  Duplicate world scans do not create duplicate facts. Only real changes of
  opted-in fields trigger material wakes.
- Save `attempted` before writing. Successful **actual Resident.send** flush is
  `pipe-written`, explicitly not model acknowledgment. Exceptions and crash
  across a write are `unknown`. No blind replay of unknown or pipe-written
  batches. A recipient can explicitly acknowledge even an unknown receipt.
- One unacknowledged awake deadline escalates outstanding facts to the issuer
  (normally JEFF), including unavailable outside-session handoffs. It does not
  retry the outside transport. No repeating “still blocked” wake.
- An exact acknowledgment covers that batch only. Later facts already pending
  require their own acknowledgment. Once all current facts are acknowledged,
  **only that obligation** settles; task completion remains `unverified`.
  Continuing work needs a separately chosen next obligation, not an automatic
  model-turn loop.
- Windows uses `QueryUnbiasedInterruptTime`, excluding sleep/hibernation per
  [Microsoft's API contract](https://learn.microsoft.com/en-us/windows/win32/api/realtimeapiset/nf-realtimeapiset-queryunbiasedinterrupttime).
  It is only read inside an existing house pass; no OS timer, timer-resolution
  change, power API or wake registration. Tests inject the clock and never
  call this API. The first sample after parent restart counts no offline gap.
  A crashed process's unobserved final interval is conservatively not counted.
- History regression/replacement and corrupt/unwritable state fail closed for
  follow-ups only. `HouseBridge` emits an explicit error class and marks its
  projection unavailable; ordinary resident/worker work continues. It never
  silently deletes the journal or establishes a replacement baseline.
- Read-only pending/receipt queries include journal/world event counts so a
  lagging projection is apparent. Only issuer/responsible-recipient rows are
  returned under existing ordinary world identity. This journal holds public
  task operational metadata, not secrets or model transcripts.

## Evidence and acceptance

Run from this worktree with the pinned interpreter:

```text
C:/Projects/Agora4/.venv/Scripts/python.exe research/text-desk-lab/notation/test_followups.py
C:/Projects/Agora4/.venv/Scripts/python.exe research/followups/staging.py
```

Tests use a real in-memory `roomworld`, actual staged Desk command/mutation
parser, real patched `House.step`, and actual `Resident.send` writing a fake
pipe. Fake clocks and process/network tripwires prevent launches/account calls.
Temporary files use `agora_tmp` inherited ACLs. No world pickle or live runtime
is read. Tests distinguish transport writes from acknowledgment.

Not verified: a live model turn, real listener delivery/acknowledgment, actual
Windows suspend/resume, or restart of a running house. No browser needed or
used. No claim that this is already available through live Desk.

## Exact deployment / reversal boundary

1. JEFF/maintainer reviews the typed contract, predicate policy and this audit.
2. **Before any integration lands**, establish an enforced lifecycle admission
   gate for HOUSE_FILES or give separately scoped explicit house deployment
   approval. The current comment/prop hold is insufficient. This patch DOES
   NOT implement or bypass that separate landing policy.
3. Check `staging.py` against the then-current source. Drift refuses. Review
   each OLD/NEW hunk in `staging.py` and the readable `integration.patch`;
   `integration.json` records the exact baseline hashes. Rebase deliberately, rerun
   bounded tests, and review `followups.py` as a new runtime dependency.
4. Only the separately approved maintainer applies the hunks. Add followups.py
   to HOUSE_FILES under that approval so later runtime changes have truthful
   lifecycle handling. No automatic patch applier or activation switch exists.
5. After authorized deployment, JEFF chooses actual task predicates/actions
   and a disposable obligation first. Observe one exact recipient ack via Desk;
   do not infer success merely from a knock or pipe flush.
6. Reversal: remove only the exact added source hunks/import, under the same
   approved lifecycle procedure. Retain followups.json and its error/receipt
   evidence; do not delete it or replay creates. No live task migration is
   necessary. The inert module and staged artifacts can remain.

House, providers, worker pool and transport source are unchanged in this branch.
Four-worker admission and user-facing browser/right-click work are untouched.

### Smallest separate lifecycle admission gate (design, not implemented)

At `Workshop.land`, before a landing flight is created or handed to
`landing.land`, re-read the card through the owner route. A deployment-blocked
card must refuse admission before any main checkout mutation. Revalidate at
the actual serialized landing admission, not only when the worker becomes
ready: a hold can arrive while a flight waits. Bind any explicit deployment
approval to that card and exact source tree, not an old branch name. Judgment
can still inspect a disposable candidate without moving main. A successful
test is not deployment approval. A refusal leaves the existing ready/held work
preserved with one truthful admission receipt.

Checking only `landed()` is too late: main has already moved, and the running
house independently detects changed HOUSE_FILES. Suppressing its restart flag
is therefore insufficient and would misrepresent the loaded code. This needs
a separately reviewed landing/owner boundary change, with held-before-ready,
hold-while-queued, changed-tree-after-approval and approved-exact-tree tests.
It is deliberately outside this implementation.
