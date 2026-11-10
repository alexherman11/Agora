# Subscription recovery and linked-chat repair, 22 October 2026

Status: activated after the guarded house reload. Jeff is configured for Codex gpt-6-astra with
reasoning=low (the installed model catalog's mapping for Alex's light request).
His saved session reports gpt-6-astra and has completed live turns. The reloaded house records session_reasoning=low. Exact model/effort metadata and
ChatGPT authentication were rechecked through the pinned runtime, and a separate
real subscription inference used the same selection.

The standard home-chat lens is live at revision 2 with an explicit-commit reply
composer. Runtime repairs below are loaded in the new house. Automatic resident quota
failover is enabled for Jeff with the explicit independent subscription fallback.

## Diagnosis and scope

- High, pre-existing prepare deadlock: Workshop handled commission=prepare before
  consuming a completed turn. prepare rejected its still-busy owner, so the event
  that would clear busy was never drained. Three existing prepare cards were paused
  through native operations; their completed results were consumed and saved.
  Turns advanced from 0 to 1, 1 to 2 and 13 to 14. All drained pending inputs.
  Their worktrees, sessions and native state were preserved. All three then produced durable prepared receipts without conflicts and returned
  to working. At the checkpoint they were queued while two other Codex workers
  occupied the available slots. This does not claim their final acceptance or
  landing completed. prepare_idle drains completion before checking ownership.
- Medium, pre-existing linked-chat defect: Ibis had appended replies, but the
  generic home-chat lens was a read-only feed. The custom ibis-corner already
  demonstrated the existing input/explicit-commit capability. The repair uses
  that capability and native append; it changes no renderer and adds no new verb.
- Medium, pre-existing misleading quota status: old Claude usage_state could be
  shown on an active Codex card. Status now checks the card's actual provider.
  The two prepare stalls were not Codex quota exhaustion.
- High, regressed protections: the October 20 house lifetime lease, uncertain
  relay barrier and worker subscription guards had lost integration during later
  changes. They are restored while preserving newer route generations and input
  interruption logic. The guarded reload loaded these protections.
- High, pre-existing uncertain CLI/MCP replay: explore.via_deskd could fall back
  to local execution after its first HTTP request committed but lost its reply.
  It now stops with an uncertain outcome and does not submit later batch lines.
  Explicit DESKD=off remains the offline path. A mock commit-then-timeout test
  verifies one submission; this is not a claim of universal exactly-once effects.
- Remaining trust boundary: native actor labels are caller-supplied, not an
  authentication boundary. This matters for exposure to untrusted callers; no
  listener, credential or security setting was changed. It does not justify
  widening access for this repair or claiming the private smoke test proves it.
- Empty resident model tools are intentional in this harness: both providers
  emit native text commands through the host relay and commission builders.
  This is not a Codex capability loss. Builder tools and provider-private session
  compaction differ; a portable handover preserves shared state, not hidden
  provider reasoning or transferable continuation tokens.

## Quota behavior implemented

quota_policy.py accepts only explicit subscription/usage exhaustion. Generic 429,
authentication, permission, transport and missing-conversation failures do not
trigger a provider switch. Idle boundaries and unresolved relay markers block
switching. The current provider pool must be held and a separately configured
provider eligible. Astra-to-Sol is not a quota escape. If no independent provider
is available, the existing usage reset pause remains visible.

Native preferred_* and fallback_* properties name exact providers/models/effort.
The policy requires quota_failover=on. It persists cooldowns, rechecks selection
before dispatch, records quota_status, and queues a deduplicated switch notice.
Return to the preferred provider occurs at an idle boundary after its hold expires.
An expired reset is eligibility to try again, not proof a future inference succeeds.

The Codex adapter requires ChatGPT subscription auth and removes API-key routing
from managed worker environments. The automatic Claude fallback validates an
existing first-party claude.ai subscription in the child's environment; API keys
are removed and custom/cloud API routing is rejected. No login, credential
generation, paid fallback or quota bypass is implemented. Startup errors back
off per resident without starving other residents.

Resident automatic return policy is distinct from the existing worker card
limit_fallback machinery. This repair preserves card-saved providers and worker
pool settings; it does not silently enable a new fallback for every worker.

## Evidence

Ran the affected suite: 158 passed, 11 subtests passed in 44.13s. It covers quota
classification/selection, reset/cooldown and both-pools-blocked cases, subscription
guards, handover and unknown-effect barriers, idle prepare recovery, house restart,
worker selection, standard chat reply and CLI/MCP timeout behavior.

Ran repository pytest: 201 passed, 2 skipped in 28.50s. New/adapter files passed
Ruff. Existing legacy files retain style debt; the repair adds no Ruff diagnostics
against their pre-edit snapshots. The documentation checker still reports the
pre-existing missing Pasted image 20260923162848.png in Dynamic Desk. Existing
generated Current Implementation has an EOF blank-line diff warning; it was not
hand-edited. After final whitespace-only cleanup, the focused chat/transport rerun passed: 6 passed in 0.50s.

Ran actual input delivery in an isolated private copy using the unchanged browser
renderer: draft, Discard, Send, committed input, empty composer, and visible reply.
One real pinned SDK turn used ChatGPT auth, gpt-6-astra and requested reasoning low.
Its native command was validated and relayed into that private copy exactly once.
Input addressed Ibis and reply addressed Alex. This was manual private turn routing,
not an automatic live-house round trip or Windows HUD/Edge acceptance. No test
messages entered the live Conversation or reached an independent resident.


Automatic-path follow-up: ran a fresh private world using the production
House.step, news/wake, Resident.send/turns_ended and House.after_turn methods,
the real Codex resident subprocess and the unchanged browser/native writer.
The trial excluded other residents, commissioned workers and host-route effects.
The resident read its charter and rested (two short startup turns), then the
browser Send committed one addressed input. The real scheduler detected a call
while resting, submitted one new Astra/low ChatGPT-backed turn, and the ordinary
relay appended one reply addressed to Alex. The same browser view displayed it
with the composer cleared. No manual provider invocation or reply relay occurred.
The private session survived the fixture-only dependency correction/restart.
No pending input or uncertain relay remained. No synthetic live Conversation
traffic, production reload or independent resident wake was used.

The initial fresh fixture omitted the live home-style role definitions; adding
that exact style and the lens's existing style binding fixed the test setup.
This is a fixture dependency, not a newly discovered production rendering defect.
It does not prove every resident-specific lens or production HUD/notification
visibility. Evidence: automatic-chat/evidence.json, automatic-chat-roundtrip.jpg,
the exact probe source and private state beneath the existing backup directory.

Evidence and targeted state backups are in
local/codex-residents/quota-repair-20261022T184627Z. The live model result is
private-roundtrip.json; the screenshot is chat-roundtrip.png. These are targeted
backups, not an October 22 full-world snapshot.

## Activation and rollback

The existing restart request initially refused full-screen Spotify. After Alex
confirmed leaving full-screen, the normal guard returned clear and the request
was re-armed. It drained all active turns, exited normally and the keeper started
house PID 58720 in place of 70960. No guard change or forced process kill occurred.
The new OS ownership lock was verified held. All 257 previously saved provider
session identities matched immediately after reload. Jeff completed new Astra/low
turns. No uncertain relay marker or startup/auth failure was present for Jeff.

All three temporary pauses were restored to their original prepare requests,
verified against the exact pause events. Durable prepare results were clean and
existing work was retained. The existing house preparation pipeline created its
own preservation/merge checkpoints; this worker did not issue manual Git commits
or pushes. Native open Desk/world state was retained through the brief scheduling
pause. Runtime activation evidence is activation-status.json beside the backups.

Jeff now has quota_failover=on, preferred codex/gpt-6-astra/low and independent
fallback claude/claude-sonnet-5-5/medium. The existing first-party Claude subscription
authentication check passed before enabling it. Simulated failover/reset/resume
passed; no real exhaustion was induced and no live cross-provider quota switch
was forced. Eligibility is checked again when a real quota hold occurs. This does
not enable a fallback for every worker card or create additional subscription capacity.

To disable automatic switching, set quota_failover=off through the native gateway.
Retain pending and relay receipts; do not replay an uncertain effect. For a deliberate
provider rollback, choose the backed-up explicit provider/model/effort and portable
handover at an idle boundary. Keep provider sessions separate. To undo the lens,
read its current revision, reconcile concurrent edits, and restore only the backed-up
home-chat text through native rewrite. To undo source, revert only this repair's
hunks after comparing concurrent work, then use the same guarded reload. Never
restore whole source snapshots or a stale world over later changes.

## Ownership

Runtime: notation/house.py, workshop.py, plan_usage.py, quota_policy.py, explore.py;
codex/codex_worker.py and associated focused tests; the native home-chat
lens and its reviewable home-chat-reply.lens source. House lease integration reuses
the existing house_lease.py. Dashboard renderer files are untouched. Dashboard
primitives and module-contract implementation belong to the other two workers.
