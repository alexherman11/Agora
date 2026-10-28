# Rowan's three-worker management slice

Builder record, 28 October 2026. The missing world word was a task-scoped resident manager entry: assigning a task to a resident did not give it a builder session or permission to call steward-only House verbs. Alex explicitly approved Rowan's two local sessions and limited management of three workers (Sentinel_46885ac60b708191a9048a25719ec998). No provider credentials, steward role, security-policy changes or paid fallback are added.

The manifest `rowan-manager-20261028.json` names three current tasks reserved by JEFF: screenshot paste into JEFF chat, dock unpinning and read-only Twitch chat. Title-bar enlargement was rejected from this batch because it overlaps the WM owner's work. The old Writing import remains held at its prior test/commit denials.

`kdesk_on.py --manager-manifest <manifest>` is an explicit one-start provisioning option. It creates a fresh member Rowan asleep, its own person session and separate builder-agent session, fresh attributed identity/charter, and private native chat. Existing sessions and residents are preserved. An independent local authority file lists exactly these three tasks; world profile edits cannot expand it. Three ordinary, revocable House `set` grants reach one card each. Rowan receives neither raw task-edit authority nor group leadership over other tasks. Re-running mismatched or revoked provisioning refuses without replacing identity or permission.

`house.manage <task> action=build|tell|retry|report|review|land|note` is the guarded entry. Only the authenticated resident person named in the approval can use it. Other members and agents representing Rowan are refused before effects. Existing House verbs keep their steward admission. The manager cannot use notes to change ownership, task scope or permission. Trusted House bookkeeping checks current authority and the revision fence, with a closed field list, then writes through the per-card kernel grant.

Worker starts, continuation starts, independent review and publication share one configurable pool (`house-settings.builder_capacity`, default two, supported one through four). Lowering capacity does not stop current work. Normal task holds, changed ownership, changed instructions, unknown outcomes and exact-candidate landing checks remain. Each worker uses the existing authenticated Codex adapter and Rowan's separate local agent session.

A terminal builder receipt wakes Rowan once per running House instance. Reading `action=report` acknowledges receipt, not task completion. Unread receipts are offered again after House restart; acknowledged receipts are not. Reporting includes bounded self-proof and its hash plus independent check receipts. Receiving, reviewing, publishing, activating and verifying remain separate. There is no background polling loop or automatic task closure.

Native tool cancellation mid-turn is still not a general revocation mechanism: the worker must check live authority before effects; host claim, phase writes, continuation, review and publication are fenced. A manager note is evidence to review, not machine-certified UI acceptance.

Validation and live activation evidence are appended below as completed. No source-only test claims a live Rowan or worker turn.
