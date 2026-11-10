# Jeff's provider handover and harness audit

## 21 October recovery: adapter changes parked during landing

The 20 October activation below is historical evidence, not a claim that every
part of that implementation remains in current main. At 23:05 on 20 October,
landing a7816 preserved conflicting uncommitted `codex_resident.py` changes only
on `parked/20261020-230555`. Main retained the new parent-owned charter receipt
path but lost Sol catalog selection and `require_subscription`. JEFF then failed
startup with `gpt-6.1-sol is unavailable`; the Codex worker failed importing the
missing subscription guard. The live house was healthy, other enabled residents
were resting, and JEFF's original conversation and unread requests remained saved.

On 21 October, outside Codex merged the preserved adapter additions with current
main's charter implementation, retaining both. It did not change model/provider,
credentials, runtime pins, the HUD, or the running house. A native call retried
JEFF through the ordinary scheduler; his saved thread stayed identical and his
completed-turn count advanced from 655 to 656 with failures cleared to zero.

Ran before activation: eight focused subscription/model/worker checks; an actual
pinned Sol runtime probe against local mock inference (zero resident tools or
injected system/developer prompt); and read-only live readiness reporting ChatGPT
authentication and Sol/medium with zero model turns. Ran after adding regression
coverage: 24 transport/charter checks passed, changed-file Ruff F/E9 passed, and
diff whitespace checks passed. A broader check found two pre-existing failures
which also reproduced before the repair: the transport fixture's empty charter
receipt and an older worker provider-switch expectation. The receipt fixture was
corrected; the unrelated worker-routing expectation is not changed here.
The required default repository suite also passed: 201 passed, 2 skipped in
27.43 seconds. The documentation checker still reports the existing missing
Dynamic Desk image. The affected Codex worker subsequently started automatically
through its normal retry; its completed work remains a separate observation.

Regression coverage in `test_transport.py` now exercises both resident model
catalogs without host tools and the worker-to-resident subscription guard import.
Private baseline, merged candidate and mock-runtime evidence are retained under
ignored `local/jeff-recovery-20261021/`. This repair needs integration into main
before another overlapping landing; leaving it uncommitted repeats the failure.
Separately, the house-side portable handover/relay/lease changes were parked in
`parked/20261020-155934` and are not restored by this narrow adapter recovery.
The earlier broad handover test results below must not be read as current-house
verification.

20 October 2026. **Activated with Alex's explicit approval.** Jeff is running
gpt-6.1-sol through Codex with ChatGPT authentication. Six live turns completed
(442 to 448); he continued his interrupted work and rested. No API fallback.

## The runtime actually inspected

**Read and observed:** the connected Windows computer is GREAME. The canonical
checkout is `C:/Projects/Agora4`, on `main`. The running keeper, door and house use
`src/text-desk/notation/`. Jeff is the existing resident named `jeff` in
Frontier, with his own corner, identity/memory notes and conversation. At inspection
his provider was Claude, model `claude-sonnet-5-5`, paused by a usage limit.

`C:/Projects/Agora` contains data and older source; its `src/agora3/jeff.py` is not
the running resident harness. `C:/Projects/ConsciousClaudeVPS` is a separate June
snapshot with an untracked local Claude Agent SDK port. Its memory-cycle engine is
not this Jeff. No VPS code or state was changed.

The current instructions and five current design documents supersede the older
Agora3 entry points supplied to this task. No `.agents/skills` directory was present
in either Agora checkout. Identification used running process paths, current code,
Git history and the repository's locked read-only world reader, not raw pickle or
transcript searches. The live charter was read. Existing edits were retained.
Other work advanced `main` during the task; the intervening changes were Windows
HUD lifecycle and friction documentation, with no overlap in this implementation.

## Implemented contract

This extends the existing Python `openai-codex==0.147.0` app-server adapter. It does
not replace the house, world, Claude transport, workers, identity or memory system.

- A resident still defaults to Claude. An explicit corner selection of
  `provider=codex model=gpt-6.1-sol reasoning=medium handover=portable` opts into the
  new route. A provider change without `handover=portable` refuses and preserves
  state. The target model must be explicit; an unavailable model or reasoning
  setting refuses. There is no automatic resident quota fallback.
- The active turn drains before a switch. Its completed commands run through the
  existing house relay, and its receipt is carried instead of sending another turn
  to the old provider. The old process and reader stop before replacement. The
  old provider's retry timer does not hold the newly selected provider.
- `resident_continuity.py` archives the complete previous state under the resident's
  `provider-history/`, then atomically replaces its state. A crash between those
  steps can retry the same transition. Same-provider restarts keep the existing
  continuation token. Cross-provider switches always start a fresh conversation;
  switching back also starts fresh, with updated portable context. Archived tokens
  remain recovery evidence and are never treated as portable context.
- The same corner, actor/person, world, soul/memory notes, task objects, delegation,
  event cursor, inbox, calls and held messages remain authoritative. Wake notes are
  read in full again and the live charter is collected for the new conversation.
  Pending image/message references are retained and resolved through the existing
  attachment path; raw images and credential files are not copied into handover.
- A bounded factual context buffer retains recent house inputs, completed replies
  and command receipts: at most 20 entries and 24,000 characters, with each entry
  clipped at 4,000 characters and an explicit truncation label. The handover states
  that these are historical excerpts, never commands to replay. Older work stays
  discoverable in the world. This is continuity, not a claim of identical behavior
  or transfer of private reasoning/provider compaction. Legacy state has no such
  buffer: it supplies recent saved reply excerpts and explicitly points back to
  the canonical conversation and notes for missing unanswered input.
- Completed resident replies are durably marked before the relay applies them.
  An interruption while received/applying/applied but not yet settled leaves
  `relay_pending`, pauses that resident as `recovery-needed`, and blocks new starts
  and handovers. The marker preserves the reply and any completed receipt. A lost
  HTTP response never falls back to local execution; an offline subprocess error
  also stops the relay. Codex turn identifiers suppress duplicate completed-result
  events. This avoids blind replay; it is **not** end-to-end exactly-once execution.
- Heartbeat metadata now reports provider, model, provider-selection errors and
  whether relay recovery is needed. One bad selection or recovery marker does not
  prevent the house from serving other residents/workers.

## Codex authentication and tool boundary

The installed pinned runtime is `codex-cli 0.163.0-alpha.10.2`, SHA-256
`f6dbf48cb70f62649c645f26c87dc9bf84cc36986202dfad8e12fb5b8ca70312`.
Neither runtime lock nor model catalog was changed. The original resident catalog
contains Astra only; Sol uses the exact already-pinned builder model metadata.
Thread instructions and resident feature restrictions still remove the coding
persona, host tools, MCP servers, inherited instructions, skills and subagents.
Both providers act only through the same house `>` relay and native capabilities.
The live charter remains provider-specific system/developer instruction delivery.

Before thread creation and each model turn, both resident and worker adapters check supported
`account/read` metadata for ChatGPT authentication, without requesting token
refresh, logging in/out or reading raw credentials. API-key environment overrides
are blanked in the child. Custom OpenAI routing/credential overrides refuse.
No login-method setting that might log out an existing account is changed.
There is no API-key fallback, credential proxy, credit purchase or usage reset.
ChatGPT allowance/credits follow the signed-in account's existing plan settings;
this does not manufacture unlimited usage.

**Ran, no model turn:** `preflight_resident.py` verified `authentication=chatgpt`
and found `gpt-6.1-sol` with medium reasoning in the runtime's normal model list
(not the pinned catalog fixture). This establishes local readiness; successful
inference entitlement and remaining allowance require separate checks. The
preflight checks the binary hash and never invokes the automatic repinning path.

Official sources read on 20 October:

- [Codex SDK](https://learn.chatgpt.com/docs/codex-sdk): the supported Python SDK
  controls local app-server and supports explicit runtime selection.
- [Models](https://learn.chatgpt.com/docs/models): `gpt-6.1-sol` is the current Sol
  identifier; access depends on plan/client/workspace. No alias was guessed.
- [Authentication](https://learn.chatgpt.com/docs/auth): ChatGPT sign-in uses
  subscription access; API keys use API billing. Forced login restrictions can
  log out mismatched credentials, so the adapter uses a non-mutating preflight.
- [App-server](https://learn.chatgpt.com/docs/app-server): thread lifecycle,
  notifications, account metadata and approvals are supported integration seams.

## Verification

**Ran:**

- 145 focused pytest checks passed in 9.00s. They cover portable round trips,
  exact model selection, legacy Claude resume, state archival, interrupted atomic
  transition, failed input/attachments, in-flight draining, provider cooldown,
  uncertain relay effects, duplicate result IDs, account rejection, charter,
  quota, context delivery and existing runtime-pin behavior.
- Default repository suite: `uv run --frozen --offline --no-sync pytest -q
  -p no:cacheprovider`: **201 passed, 2 skipped in 27.43s**. No dependency install.
  The default suite covers the older native runtime; the research tests above
  supply evidence for the current desk.
- Standalone worker pool, persistent-builder and wake-fold scripts each printed
  `all passed`. These use isolated fixture worlds/processes; no live model.
- Actual pinned-runtime probes for Sol and Astra each passed against loopback
  mock inference with empty scratch profiles. Each compiled request contained no
  tools, no system/developer prompt and exactly the supplied user input; completed
  text reached the house protocol. These are real runtime tests, not real model
  behavior or live Jeff tests. See `resident-provider-evidence.json`.
- Ruff passed for `src`, `tests`, `scripts`, the adapter/probe and all new files.
  The two touched legacy modules already have extensive style debt: comparing
  against their pre-task source found **zero new diagnostics** (house 362 to 357;
  workshop 463 to 463). No broad reformat was applied.
- The documentation checker reports the existing missing
  `Pasted image 20260923162848.png` reference in Dynamic Desk. This was already
  recorded in the existing runtime README. Unrelated design text was preserved.

During verification, three existing context-delivery tests failed because their
fixture allowed the newly added charter receipt to call the real Desk transport.
The same three failures reproduced against the pre-task house source (3 failed,
5 passed). The fixture now stubs that receipt and explicitly rejects real Desk
calls. No live world write occurred: its existing subprocess mock rejected the call.
The first broad pytest collection also included standalone scripts that exit;
those scripts were subsequently run through their intended entrypoints.

**Ran live after explicit approval:** two private subscription-backed Sol turns,
including runtime restart/resume and exact fixture-token recall. Then a controlled
idle-house reload, native Jeff switch (e13620), and six actual completed Jeff turns.
Only the house was reloaded; the existing keeper started PID 36324. All 18 old child
processes exited after pipe closure. Desk, HUD, keeper and unrelated services stayed
up. No credential generation/copy, security-setting change, permission expansion,
source commit/push or independent agent contact was performed.

**Not run:** live return to Claude (its quota is exhausted), forced mid-effect
recovery, live compaction on the new Jeff session, or Windows reboot.

## Prioritized audit

| Priority | Finding and practical consequence | Disposition |
|---|---|---|
| P1 | A first-line HTTP timeout could execute the same command again locally; later failures claimed the uncertain line had not run. | Fixed: no HTTP retry/fallback, durable relay barrier, explicit reconciliation. Offline transport errors also stop. |
| P1 | Provider IDs were correctly bound, but switching could only refuse; quota retries dropped the portable body of delivered unanswered input. | Fixed: explicit handover, archived tokens, full unresolved inputs and attachment references. Readiness review caught and fixed clipping of long unresolved input before activation. Jeff's single legacy input was recovered exactly; other legacy gaps remain explicit. |
| P1 | Codex resident startup accepted whatever auth the profile/runtime selected. | Fixed for both managed Codex residents and workers: ChatGPT checks before thread creation and each turn, API environment masking, custom route refusal. This guards model transport billing; arbitrary worker tools are not a global spending firewall. |
| P1 | `House.another_house` is a heartbeat/PID check, not an atomic OS lease. Two simultaneous starts can race and run the same resident. | Fixed with a process-held OS lease for the entire house run. Real Windows contention, distinct-world independence and release after forced fixture-process death passed. The deployed house holds its lease; the heartbeat check remains for upgrades from older houses. |
| P1 | Native actor names are caller labels, not authenticated identities. The relay supplies Jeff's name; broad world verbs and commissions can cause external effects. | Existing prototype boundary, not the older Agora3 gateway guarantee. Resident zero-tool isolation is verified, but does not turn the entire world into a security sandbox. No permissions were broadened. |
| P2 | Pipe flush is recorded as delivery before provider acknowledgement. A crash can leave an unanswered count for an input the provider never accepted. | Complete unresolved inputs improve cross-provider recovery. A provider-acknowledged delivery/outbox protocol is still needed for stronger same-provider guarantees. |
| P2 | Lost-conversation recognition is a Claude stderr-string heuristic; Codex missing-thread recovery remains ordinary backoff. | Existing limitation. Preserve state and explicitly hand over/reconstruct; do not silently reset on arbitrary errors. |
| P2 | Compaction and model behavior differ; the house has bounded excerpts, not semantic long-term-memory extraction or comprehensive task summaries. | Intentional small scope. World notes/tasks stay authoritative. Automatic memory consolidation is a separate design decision. |
| P2 | Quota text parsing and five-minute retries when reset time is unknown are heuristic. No resident provider switches automatically. | Preserved explicit selection; new provider starts use its own cooldown. Test real quota/auth episodes before enabling automation. |
| P2 | Charter unavailability currently reports a warning and proceeds. Child runtime cleanup is weaker for residents than the workers' OS job containment. | Existing behavior, unchanged. Decide whether missing charter should block, and extend lifecycle containment if required. |
| P3 | Diagnostics include provider-specific raw stream/error text and persistent transcripts. Rotation/redaction is not a complete policy. | No credentials were inspected or copied in this task. Audit retention and redaction separately; new preflight emits only selected metadata. |

Scheduling remains the house's wake/news/rest system. The existing `timers=off`
option prevents time-based wakes; this work does not change it, the worker pool,
worker grants, landing policy or supervisor. Provider independence here means
shared identity/state/capabilities, not identical model judgments or equal SDKs.

## Setup, switch and rollback for the operator

These are operator instructions for later switches; Alex approved and this task
completed Sol activation on 20 October. Alex should not be asked to type commands.
No installation or new login was needed. Do not repeat activation to check status.

1. Review this source diff and preserve unrelated edits. Run the checked-in
   `preflight_resident.py` with the pinned repository interpreter. If sign-in is
   missing or model access refuses, stop for an approved login/access decision;
   never substitute a model or an API key. Run the approved private live fixture
   before changing the live corner; no test messages belong in the Conversation.
2. With specific approval, let outstanding work settle, take normal runtime/state
   backups, and reload the house through its existing controlled lifecycle. This
   task did not commit source. Do not manually run a
   second house beside the current one.
3. Resolve **JEFF's corner** through the native Desk and inspect its current
   provider/model/wake settings. In one native property operation set
   `provider=codex model=gpt-6.1-sol reasoning=medium handover=portable`.
   Keep actor, identity/memory/wake references, world and permissions intact.
   The next house pass drains the old turn and performs the state transition.
   This setting permits a fresh Codex conversation and uses subscription allowance.
4. Verify the house status reports Codex/Sol, the archive exists, the new session
   has a different provider token, and the first wake includes the same identity,
   charter, full memory notes, queued request and any attachments. Perform one
   explicitly approved harmless private fixture before live Jeff work. Never put test messages into Alex and Jeff's Conversation.
5. To return to Claude, make the corresponding explicit native property change
   with the intended Claude model (at inspection: `claude-sonnet-5-5`) and
   `handover=portable`. It drains Codex and starts fresh Claude context from current
   state. It does not restore old world data or replay the archived Claude session.

For code rollback, use the reviewed source diff to revert only this task's edits
after a controlled stop; preserve provider-history and current world/session data.
If a switch has already occurred, first complete the explicit handover back to
Claude while this implementation is installed. Reverting source does not convert
provider session IDs.

For `recovery-needed`, an operator must keep the resident stopped, preserve its
state and transcript, compare `relay_pending` and recorded receipts with the world
history, and determine which effects occurred. Do not replay the batch or clear
the marker by guesswork. Store a reconciliation receipt for the next wake, then
clear the marker only after that review. An operator recovery UI/verb is not yet
implemented; this conservative stop is a remaining usability limitation.

## Verified activation and remaining boundaries

**Activated with Alex's explicit approval on 20 October 2026.** Jeff's existing
Frontier corner f5189 now uses Codex gpt-6.1-sol, medium reasoning and ChatGPT
subscription authentication. Native selection event e13620; reloaded house PID
36324. Six live turns completed (442 to 448), after which Jeff rested.

The adapter supports explicit portable handovers. The house drains the old turn,
retains receipts and complete unresolved inputs, archives the old provider state,
and starts a fresh conversation. Same-provider restarts resume their own token.
Identity, world notes, tasks, permissions, cursor and queues remain canonical.
Bounded recent context is historical data, never a replay script. Provider-private
reasoning and compaction do not transfer. Claude remains the resident default.

Managed Codex residents and workers require ChatGPT authentication before thread
creation and each turn, mask API-key environment overrides, and reject custom
authentication routes. Unavailable exact models refuse; pins were unchanged.
Resident host tools remain empty, matching the existing Claude relay architecture.
Native commands and delegated builders remain available through the world.

The house now holds a per-world OS lifetime lease. Completed replies leave a durable
relay marker until settled; an uncertain effect pauses for reconciliation instead
of retry or HTTP-to-local fallback. There is no exactly-once guarantee or interactive
reconciliation UI. Native actor labels remain unauthenticated. Worker tool/approval
parity and provider delivery acknowledgement remain pre-existing limitations.

**Ran:** 145 affected pytest checks passed in 9.00s; root suite 201 passed, 2 skipped
in 27.43s; worker-pool, builder and wake-fold scripts passed. Actual compiled-runtime
mock probes verified Sol/Astra empty resident tools. Two private live Sol turns
verified subscription inference and restart/resume, without world access.
The first actual Jeff input contained all 77 nonempty charter/soul/memory lines
and the exact 6,633-character interrupted request. All 167 other saved session IDs
were unchanged. The input contained 36,369 characters; identity references and
canonical memory notes were unchanged. No test message entered Alex's Conversation.

Jeff continued his earlier charter work: events e13637-e13643 removed redundant
charter reads from wake strings. His recorded changes preserved the dedicated start
hook and injected rules; this was post-activation work, not lost handover state.

Backup: local/codex-residents/before-activation-20261020T213254Z, with locked world,
170 state files, original settings and rollback evidence. Only the idle house was
reloaded; all 18 old children exited on pipe closure, without extra termination.
Desk, HUD and keeper stayed up. Claude residents remain quota-paused with their
session state preserved; the reload did not switch them to Codex.

Return to Claude through one explicit native property change on f5189:
provider=claude model=claude-sonnet-5-5 handover=portable, once its allowance returns.
The handover drains Sol and uses current world state in fresh Claude context.
Do not restore stale world data or resurrect the old token. A source rollback
must follow a completed return to Claude and controlled stop, preserving unrelated
edits, provider archives and current state. Live return to Claude, new-session
compaction and mid-effect recovery remain untested. No credentials, permissions
or security settings changed; no paid API fallback, source commits or pushes.
The existing missing Dynamic Desk image still fails docs checks; changed-file
Ruff passes, with no new legacy-house/workshop diagnostics.

See [the full handover/audit](../src/codex/resident-provider-handoff.md)
and [selected evidence](../src/codex/resident-provider-evidence.json).

The empty resident tool inventory is intentional, pre-existing parity with
Claude's empty tools selection, not lost native capability. Completed command
lines still use the same native relay. Coding workers are different: pre-existing
Codex workers have native shell/edit/web tools with workspace-write and
approvalPolicy=never; Claude workers use an allowlist and per-card extra grants.
These are not identical security mechanisms. Actor labels and broad tools need
separate design before treating untrusted local code as isolated. They did not
block this private test or switch: no actor authority or worker tool grants changed.

Historical context remains bounded, but complete unresolved inputs are retained
separately until a successful result, without clipping. The exact 6,633-character
legacy input was recovered through its targeted private transcript event; raw
transcripts and credentials were not copied into source.

The first live runtime init recorded exact Sol, ChatGPT authentication and empty
tools. Its developer charter matched the saved live charter. Full-note checks:
standing rules a6529 21/21 lines, soul a5191 53/53, memory a5193 3/3. The new token
differs from the archived Claude token. No relay-recovery marker or retry remained.

The activation summary and rollback were also recorded through native operations
in Handbook section a6986. Other Handbook content and unrelated local edits were preserved.
