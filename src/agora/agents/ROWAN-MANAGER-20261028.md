# Rowan's three-worker management slice

Builder record, 28 October 2026. The missing world word was a task-scoped resident manager entry: assigning a task to a resident did not give it a builder session or permission to call steward-only House verbs. Alex explicitly approved Rowan's two local sessions and limited management of three workers (Sentinel_46885ac60b708191a9048a25719ec998). No provider credentials, steward role, security-policy changes or paid fallback are added.

The manifest `rowan-manager-20261028.json` names three current tasks reserved by JEFF: screenshot paste into JEFF chat, dock unpinning and read-only Twitch chat. Title-bar enlargement was rejected from this batch because it overlaps the WM owner's work. The old Writing import remains held at its prior test/commit denials.

`kdesk_on.py --manager-manifest <manifest>` is an explicit one-start provisioning option. It creates a fresh member Rowan asleep, its own person session and separate builder-agent session, fresh attributed identity/charter, and private native chat. Existing sessions and residents are preserved. An independent local authority file lists exactly these three tasks; world profile edits cannot expand it. Three ordinary, revocable House `set` grants reach one card each. Rowan receives neither raw task-edit authority nor group leadership over other tasks. Re-running mismatched or revoked provisioning refuses without replacing identity or permission.

`house.manage <task> action=build|tell|retry|report|review|land|note` is the guarded entry. Only the authenticated resident person named in the approval can use it. Other members and agents representing Rowan are refused before effects. Existing House verbs keep their steward admission. The manager cannot use notes to change ownership, task scope or permission. Trusted House bookkeeping checks current authority and the revision fence, with a closed field list, then writes through the per-card kernel grant.

Worker starts, continuation starts, independent review and publication share one configurable pool (`house-settings.builder_capacity`, default two, supported one through four). Lowering capacity does not stop current work. Normal task holds, changed ownership, changed instructions, unknown outcomes and exact-candidate landing checks remain. Each worker uses the existing authenticated Codex adapter and Rowan's separate local agent session.

A terminal builder receipt wakes Rowan once per running House instance. Reading `action=report` acknowledges receipt, not task completion. Unread receipts are offered again after House restart; acknowledged receipts are not. Reporting includes bounded self-proof and its hash plus independent check receipts. Receiving, reviewing, publishing, activating and verifying remain separate. There is no background polling loop or automatic task closure.

Native tool cancellation mid-turn is still not a general revocation mechanism: the worker must check live authority before effects; host claim, phase writes, continuation, review and publication are fenced. A manager note is evidence to review, not machine-certified UI acceptance.

Validation and live activation evidence are appended below as completed. No source-only test claims a live Rowan or worker turn.

**Adapter correction found by real execution:** Rowan's first live Codex turn completed but could not discover its world tools (`unsupported call`), so it launched nothing. The pinned worker adapter already uses the supported code-mode discovery wrapper. The resident now opts into that wrapper only when explicitly given the native Agora MCP configuration; exactly see/do/lines are enabled. Native shell/files/web/computer/subagent tools remain disabled, legacy tool-less residents keep their original configuration, and subscription authentication is unchanged. **Ran:** 12 adapter/worker tests passed in 1.32s. This is a transport fix for the existing world tools, not added task authority.


## Live checkpoint, 28 October

**Ran:** the committed manager implementation (`4c259b5d4`) and resident transport correction (`a34a3e4e`) are active. Native Rowan is person `dk1190`, agent `dk1196`, private chat `dk1194`, Codex session `01a1842e-15f0-7521-bdc5-45fc7c6a5e7a`. The live House admitted three actual authenticated Codex turns, not just queued requests:

| Board task | Run | Codex session |
|---|---|---|
| Screenshot paste into JEFF chat (`dk1017`) | `kernel-dk1017-ecb96f9ad0` | `01a18432-387d-7d41-a3a1-fd5756d18218` |
| Dock Unpin (`dk1144`) | `kernel-dk1144-30394317b4` | `01a18432-456a-7373-aa65-da32d65a292f` |
| Twitch chat (`dk1140`) | `kernel-dk1140-229d1df9ea` | `01a18432-55b6-7010-a85a-2d2fd1c067f3` |

The first-launch snapshot is `modules/house/evidence/rowan-workers-20261028.json`; the later checkpoint is the adjacent `rowan-workers-checkpoint-20261028.json`. These contain no credentials. The setup Board task is `dk1158`. Readback verified owner Rowan, lead `dk1190`, real run/session identities and source changes for all three tasks.

**Ran:** provisioning added exactly two local sessions, retained existing credentials and JEFF/Sable session identities, and preserved all 14 world window records. No provider credentials, paid fallback or steward role were added. Zero world draft records existed before and after; this does not prove browser-local unsent text preservation. Active worker turns were not interrupted.

**Read:** Rowan received Unpin and Twitch self-proof, requested source-only audits, and retained their test holds. Screenshot and Twitch both touch kernel `chat.py` and `words.py`; Rowan arranged screenshot-first, fixed-SHA handoff and serial review/publication. Receipt means a returned worker result, not verified behavior. No feature from these three workers has yet been declared landed or activated.

**Read, exact blockers:** Unpin printed `1 passed, 2 warnings, 9 errors in 1.40s`; setup was denied creating `C:/Users/Alex/AppData/Local/Temp/kdesk-test-hqpai3wh/world`. Twitch printed six setup errors in its adapter suite and five in existing chat tests, at system-Temp `kernel-twitch-*/log` creation. No behavior assertion ran in those suites. Their syntax/parser checks are narrower evidence. The worker configuration uses Windows `unelevated`, `workspace-write`, approval `never`, with a deny handler. No change to those restrictions or alternate scratch route has been applied. JEFF's proposed worktree-local scratch fix is explicitly held, not approval to retry. The old Writing import denials remain separate. Twitch also needs an owner-confirmed channel; the checked-in adapter is parameterized and does not name Alex's channel.

**Ran, manager tests:** the initial isolated manager and lifecycle proofs passed, including 73 tests in 23.54s, final manager-only 19 in 0.75s, provisioning/move/desktop 47 in 48.89s, a private actual-House nine-check proof with no model turns, and 12 transport/worker tests in 1.32s. These are overlapping suites, not additive totals. A later combined test order exposed a test-only mock defect: `test_move_resident.py` then the manager launch case printed `1 failed, 7 passed in 1.90s` because patching process-wide `Thread.start` counted unrelated fixture threads. The manager/capacity tests now mock only the builder's imported threading namespace and assert actual requested tasks. The formerly failing order plus both affected suites printed **43 passed in 2.21s**. Runtime source and sandbox policy did not change for this repair.


**Later receipt and native review:** Screenshot returned `BUILD-RESULT.md`: five in-memory image-adapter tests passed in 0.084s; seven kernel chat fixture tests failed at setup with WinError 5 under system-Temp `kernel-chat-*/log`. No denied retry or browser acceptance ran. All three workers now have source handoffs; source-only correction turns can continue while fixture execution stays held. Rowan identified concrete Unpin defects (stale reorder writes, detached menu cleanup, launcher visibility) and an overly broad widget undo grant. JEFF refused that grant and requested a normal user-act design with existing user undo. No expanded undo grant was activated. This is observed manager review and correction, not a claim that the corrected feature works. Shop receipts/messages `dk1228`, `dk1230`, and `dk1233` preserve that handoff.

Remaining decision: authorize the narrowly described fixture-harness repair and one retry of the three new task suites, if desired: harness-owned scratch under each existing worker worktree, without wider writable roots, elevation, credential changes or replay of the old Writing operations. No such relocation or retry was performed. Existing user authorization to create Rowan and run three workers is fulfilled; their end-user feature acceptance remains held pending the exact denial resolution and ordinary review/activation.
