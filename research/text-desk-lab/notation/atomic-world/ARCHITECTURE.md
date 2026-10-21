# Atomic data admission — internal engine prerequisite

20 October 2026, worker-a7666. Source only; no public command, HTTP route,
live migration, carry affordance, or partition adapter is enabled.

## Decision and alternatives

Ordinary independent commands deliberately retain earlier successful lines when
a later line refuses. Therefore create followed by placement cannot implement an
all-or-nothing pickup. Compensating removes are insufficient: another reader or
rule could already have observed the create, and compensation can itself refuse.

| Boundary | Benefit | Missing or unsafe part |
| --- | --- | --- |
| A single typed promotion operation | Smallest public vocabulary; can validate source, receiver and preview together | Accepted partition planner/schema is absent in this base. Inventing placement here would bypass that contract. |
| Arbitrary transaction command text | Reuses all existing verbs | World verbs, hooks, file/host effects, unbounded rules and nested commands cannot safely run during preparation. Rejected. |
| Bounded internal native data envelope | Exercises real Desk checks and real persistence now; later typed promotion can use it | Needs a reviewed public adapter and accepted partition preview integration before pickup can use it. Chosen. |

This is an engine prerequisite, not certification of item dragging. A typed
promotion adapter remains the intended public boundary. It must admit only a
world-approved source/view and legal receiving layout, use pickup-time fences,
dedupe/restore within the current workspace, and construct the exact accepted
partition plan. A successful kernel call does not establish those policies.

## Programming interface and limits

`deskd.Session.atomic(operation_id, observed, steps)` is available only inside
this thread's active ordinary writer Session. `atomic_status(operation_id)`
reconciles without creating. `atomic_undo(new_id, observed, original_id)` admits
whole-record undo through the same boundary.

These are internal Python entry points, not caller authentication. There is no
new Desk word or `/api/do` dispatch branch. Object handles, hashes, actor props,
and the in-memory loader used by tests are not security boundaries.

`atomic_world.capture(desk)` is a conservative before-state fingerprint of facts,
events, revisions, allocation counters, actor and window. Capture it when the
intent is observed, retain it with that intent, and do not refresh it at drop to
hide intervening changes. It rejects unrelated mutations too; no large-world
latency or fine-grained concurrency claim is made.

The envelope contains 1–16 typed steps, at most 32 KiB of request data, and a
16–80 character stable operation identity. Targets are literal appearance/surface
IDs or earlier `@alias` create results; no selections or command text:

* `create`: a surface with title and free/row/column layout; or an untagged
  `kind=note role=home-panel` with title, current writer actor, lens, optional
  literal observed `shows` and yes/no `shelf`. No text, tags, wake, grants, kinds,
  verbs, arbitrary role, or another actor.
* `prop`: declared surface data fields (`target`, `lens`, `workspace`,
  `panel_state`, `layout_state`, `panel_order`, `shows`, `shelf`); own untagged
  home-panel notes allow only `shows`, `lens`, `shelf`. These surface field names
  are not a claim to implement the pending partition schema.
* `move`: one literal `into` surface. Existing native permission, observation,
  destination, revision and structural checks still apply.

Real home-base panels are **notes**, not surfaces: see live home-tiling and
drop-panel, and hud-equal/apply.py. Their target is `shows`, not a generic
`target` prop. The tests separately exercise both subject and appearance
allocation, restore and deletion. Note role/actor cannot change through this
envelope. Existing unrelated notes, other actors' panels and tagged notes refuse.

## Admission, visibility and failure

1. Hold the existing Session writer serialization throughout. Require an
   established recoverable journal and snapshot marker, not automatic genesis.
   Reject nested ordinary command/rule contexts.
2. Fsync and recover the journal into a detached Desk. Verify its facts and
   digest agree with the journal before publishing recovery. Check the durable
   actor/window/operation receipt first; the same request returns its original
   result even after other changes. Reusing its ID for different input refuses.
3. Check the observed fingerprint. Deep-copy the real Desk. Use its actual
   `cmd_do_knife`, ordinary permissions, fences and native mutation machinery.
   A referenced `shows` source must exist and have the writer's current observed
   revision. Temporary allocations, events and rule state remain on this copy.
4. Run rules on the candidate only after final explicit placement. Native rule
   actions share the same whitelist and 16-action budget. A world-verb rule,
   custom mutation hook, unsupported action, refused action, or unsettled rule
   chain refuses the entire candidate. Ordinary rules/batches are unchanged.
5. Recheck original actor/fingerprint without releasing the lock. Construct one
   record containing final before/after facts, every native event, rule state,
   allocation counters, request digest and operation receipt. The 256 KiB record
   limit refuses oversized results before append. Facts are grouped on the
   first part; remaining parts retain event/rule cause and full event metadata.
6. Strict `Log.append` flushes/fsyncs this single record; it does **not** use
   `safe_commit`, whose ordinary error policy would be wrong here. Publish the
   candidate only afterward, while still holding the writer lock.

A preparation refusal publishes no own facts, allocations, events, rules,
notices or effects and appends no receipt. It may first recover earlier durable
work. IDs of committed operations are not reused after undo.

A write/fsync/publication failure is **unknown**, not an ordinary refusal.
Poison and evict the Session so its exit cannot save an old world over a
possibly durable record. Reopen and call `atomic_status` using the same identity:

* Full record: recover final state, events, rule cursor and original receipt;
  never create again. A matching retry also returns that receipt.
* No complete record: status is absent; the original fingerprint/intent still
  needs validation before any retry. A partial tail is removed on append.
* Unreadable or inconsistent journal: fail closed as unknown; require repair.

This relies on the existing log filesystem/fsync contract, not a new database
or multi-file transaction. No external effects or effect callbacks participate.
The partial-tail fix searches past 64 KiB, because bounded atomic records may
exceed the old scan window.

## Rules, events, observer and undo semantics

Native events still exist individually but are published together. Rules see the
final explicit state, not an exposed half-created panel. Rule-generated native
facts and events belong to the same record. Rule state and full native event
metadata are recovered with an atomic record so duplicate retry does not re-arm
its firings. This does not fix or promise global exactly-once delivery across
ordinary historical records.

Custom hooks refuse rather than being silently bypassed. No observer callback is
dispatched by this kernel after publication; log consumers can read the durable
record. Any future adapter must review observer integration before activation.

Undo uses real `store.undo_plan` and the record's facts, including rule changes.
Later conflicting facts or references refuse before publication. Every grouped
event is marked undone. Primitive World.undo fallback refuses atomic events;
there is no child-event compensation path. Ordinary journal undo can also undo
the whole group. Recovery marks undo targets undone so retry cannot resurrect
them. Rule cursors are not rewound as if the operation never happened; undo is
itself an admitted event, and eligible rules may react on the final undone state.

## Evidence and remaining integration

**Ran:** `test_atomic_world.py`: 36 tests, real Desk/World, real Log, real
Session admission and writer locks. Only the Session loader is replaced by an
in-memory loader. Fixtures use fresh inherited-ACL directories below the
worktree, outside supplied sessions. Cases cover real note-panel and surface
success/restore; late refusal without subject/appearance/ID/event leaks; observed
source/actor/permission checks; unsupported effects; stale membership/layout;
concurrent stale and duplicate requests; rule visibility, refusal and recovery;
complete/partial/lost replies and failed fsync; whole undo and changed-fact
refusal; independent ordinary line behavior.

**Ran:** existing `test_rules.py` printed `all passed`; `test_deskd_reads.py`
printed `all ok`; full `test_store.py` printed `all passed`, including its
disposable CLI/server/concurrent-writer/crash-recovery fixtures. The latter two
used an inherited-ACL temporary-directory shim (`agora_tmp.directory`) because
Windows tempfile mode 0700 excludes this sandbox token. No production process
was queried, started or stopped. `git diff --check` passed.

**Read:** real mutation, rules, Session, journal, undo implementations; live
home-tiling/drop-panel; item-carry architecture/checkpoints. No private world
session file, host query or painter source was used.

Not run: supplied-world health (this commission excludes session-file access),
live activation/migration, representative large-world timing, painter/browser or
partition acceptance. There is no wired gesture to demonstrate in this change.

Remaining before a public pickup route:

1. Accepted tiling/partition schema and planner; typed adapter source and
   receiver/source/layout membership fences using its original paint contract.
2. Restore/dedupe policy, actual preview/final placement agreement, copy-only
   integration and guarded browser acceptance with a7606/a7045.
3. Review custom-rule/hook compatibility, log-observer integration and bounded
   full-world fingerprint cost on a disposable representative world.
4. All writers/recovery readers must understand atomic record metadata before
   enabling any caller. Old runtimes are not safe participants merely because
   they can replay facts.

No endpoint, world patch, live migration, pointer affordance or runtime activation
is part of this commission.
