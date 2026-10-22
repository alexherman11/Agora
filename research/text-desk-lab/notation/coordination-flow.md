# Resident and worker coordination, 21 October 2026

Alex asked outside Codex for dependable task handoffs, concise worker reports,
capacity yielding, clearer blockers, and ordinary human follow-ups queued after
the current response. This is an implementation record, not a new design mandate.

## State

**Activated**, with Alex's explicit approval, from main commits `a44450e` and
`952629e`. No push. The desk accepted both versions through its health-checked swap;
the keeper reloaded the house normally. JEFF completed turns on Claude Opus 5.5,
with the actual runtime reporting that exact model and zero host tools. His old
Codex state/token is archived, his new session is distinct, and the handover packet
cleared after a successful result. All 218 other pre-existing state files retained
their session tokens; none were missing. Keeper, door, home supervisor and HUD
process creation identities remained unchanged.

The first reload finished without cutting a turn. The snapshot-routing correction
needed a second reload, whose 90-second grace limit interrupted Rowan and four
workers. All five resumed from saved conversations; this is not a claim that their
tasks finished. Same-provider reload kept JEFF's new Claude conversation.

Already live through native operations: the concise collaboration guide;
`assign-task`, `accept-task`, `block-task`, `worker-update`, and `yield-work` notes;
the actionable commission view excludes reported/done/landed/cancelled records.
Records and evidence remain present. The missed baseline checkpoint was explicitly
routed to Juniper for review, without resuming that paused commission.
Juniper subsequently acknowledged both coordination gaps and explicitly resumed
the worker through ordinary admission, preserving its health/baseline requirements.
The house recorded its normal resume charter receipt. This confirms lead receipt
and a chosen next action, not completion of the baseline work.
Automatic transition wakes are active. A real implementation checkpoint produced
one native wake record and JEFF's acknowledgement on the task (e20373, e20374,
c8983). No test message was sent to Alex's Conversation. Workers have begun adding
topic links to the new documentation index (e20397).

## Contract implemented

- `reply_policy=queue` on a chat opts into ordinary human follow-ups arriving in
  order after the current reply. Unknown/absent policies retain existing behavior.
  Explicit other recipients and worker chatter retain their existing semantics.
  Enabled on the Conversation at e20129. Recent actual human message routing was
  checked against the live policy; ordered mid-turn behavior was tested in fixtures.
- Leading stop/cancel/correction directives invalidate pending turn commands.
  The parent checks before relay; Desk dispatch rechecks under its native lock.
  This does not cancel an in-flight provider request or undo an effect. Host-route
  effects and CLI specials outside Desk dispatch lack the same locked boundary.
- Human follow-ups in opted-in shared chats wake their resident recipient without
  requiring an @ header. Native receipts say queued/wake requested, not delivered.
- Task owner changes, explicit owner acceptance, material states, blockers and
  explicitly authored milestones produce bounded notices to the responsible lead
  or resolver. House cursor/inbox persistence handles each event once normally.
  Acceptance is a recorded owner action, never inferred from a knock. Actor labels
  retain the existing world trust model; this is not new authentication.
- `block-task` requires a blocker, resolver and resume event. Incomplete calls make
  no partial change. Existing tasks are not silently assigned or resumed.
- `commission=yielded` cooperatively releases capacity and becomes eligible when
  capacity returns, respecting priority, retry, permissions and existing worktree.
  `paused` remains an explicit hold. Blocked/approval-held work does not auto-resume.
  `yield-work` is installed. The plan fuel hold is checked before consuming input
  or resuming; clearing it permits the next eligible turn.
- Worker prompts start with a concise collaboration guide and a worker-maintained
  documentation index; workers organize focused topic notes and retrieve relevant
  detail on demand. The old catch-all notebook is preserved as historical source,
  with its append-everything instruction explicitly superseded in the live world.
  Summaries lead with outcome/blocker, consequence and
  next action; full evidence remains world-readable. No extra summarizer model.
- Inbox/wake input and attachment references remain durably staged until pending
  delivery is saved. Restart recovers an unsent handoff. A crash between pipe flush
  and saving its marker may replay input: no exactly-once model-delivery guarantee.

## Verification

Ran: 113 affected pytest checks plus 11 subtests passed in 14.51 seconds, including
real native verb execution in disposable worlds, task routing, interruption gates,
worker capacity arbitration, crash/pipe-failure recovery and message context.
No test message entered Alex's Conversation. Live model activity was the approved
handover/resumption and the real implementation handoff, not a synthetic chat test.

The initial root suite reported 200 passed, 2 skipped, one timing-sensitive failure
in `test_midturn_delivery_and_explicit_peer_collaboration`; its focused rerun passed.
The full rerun passed: 201 passed, 2 skipped in 27.72 seconds. After the final
conversation-loss attachment fix, 18 recovery/conversation/context checks passed.
After provider integration and the yielded-worker fuel hold correction, 125 affected
tests and 11 subtests passed in 15.07 seconds. The root timing failure recurred;
inspection showed peer `work.send` intentionally queues delivery (`deliver=False`)
for steering outside the world authority lock. Its test now waits for actual peer
delivery with the existing bounded `until` helper, rather than assuming another
worker's synchronous receipt implies that peer delivery has happened. Runtime code
is unchanged by this test correction.
The final root suite passed: 201 passed, 2 skipped in 26.22 seconds.
Live verification exposed an omitted production storage shape: task event snapshots
are externalized into the undo archive. `kept.copy_of` now loads them, with an actual
SQLite archive regression covering assignment, later reassignment, milestone routing
and House.news. The final combined affected suite passed 126 tests plus 11 subtests
in 16.17 seconds. The first checkpoint did not wake its lead; a fresh checkpoint
after the correction did. Historical events were not replayed to manufacture delivery.
The documentation checker reports the existing missing Dynamic Desk image.
Changed-file Ruff F/E9 reports four existing desk/workshop diagnostics; new helper
and test files pass. Diff whitespace checks pass.

Pike's separate worker delivery-record task and Sable's latency task remain staged
with overlap notices; this change does not claim their work is integrated.
