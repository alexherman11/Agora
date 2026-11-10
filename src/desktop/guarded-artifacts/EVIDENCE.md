# Evidence and limits — 21 Oct, worker-a7940

**Read:** `image_comments.py`, `house.Resident.send/hold_unanswered`,
`House._knocked/news`, `desk_knife.py`, `deskd.py`, `world.py`,
`message_context.py`, `desk_mcp.py`, `codex_resident.py`,
reviewed model catalogs/locks, and `combined-review/journeys.py`.
Both adapters already have actual image input; no new inference/capture API is
necessary. The native host-route capability is disabled pending separate review
and remains disabled.

**Ran:** targeted selector/image-comment tests: **38 passed** (including the
existing 10 image-comment tests). Coverage includes preflight with no world
effects, delivery through real Desk dispatch, actual image content through
`Resident.send` and Codex `resident_inputs`, persisted pending refs, saved-session
recovery, unchanged text input, provider refusal before file access, hashes,
traversal/URL/arbitrary-file refusal, missing/report/Guard checks, bounded bytes,
dimensions, APNG, decode failure, malformed reports, revision fences, worker
off-boundary and reparse-point refusal.

Initial fixture run hit Windows owner-only pytest temp ACLs; tests now use
existing inherited-ACL `agora_tmp.directory`, not permission changes.
Broader unchanged `codex/test_transport.py`: 5 pass, one existing
`codex_worker.require_subscription` AttributeError; two model-selection fixtures
cannot create their pytest temp directories (WinError 5). These are not claimed
as a full adapter-suite pass.

**Ran, genuine artifact on disposable in-memory world:** named screenshot
`combined-review/2026-10-20-225210-1280x800/01-busy-declined.png`;
211176 bytes, 1920×1242, SHA-256
`363265a1d1483adc6b5970c576380d616721de4f99bbfb9a4f3a1e34974549d3`.
Report SHA-256
`203d1c546a6c87e8fba5b2779454866a84cfd2978a54fabb774115052fb71f61`;
Guard exit 0, “alex: untouched by the sandbox …”; journey `busy`, passed.
Viewport recorded 1280×800; legacy report's world event is null, not invented.
Validated/decode-checked the exact image, attached through native comment dispatch,
resolved an actual image block of **281568 base64 characters**.
The first isolated attempt correctly refused an unseen target; after reading
the fixture target, the isolated comment succeeded. No live effect was repeated.

**Looked:** opened those exact existing pixels. Independently visible:
Connect Spotify / Nothing playing tile at left, Viewer with The lowdown selected,
JEFF thinking card at right, Board below, and a Viewer drag tooltip.
These details are a builder's visual check, not a resident receipt; the host
proof prompt intentionally does not supply them.

**Blocked:** CLI preflight in this worker refuses `DESKD=off` before any network
request. No live attachment was sent, resident confirmation remains pending.
The README gives the one permitted host-side proof command. No settings change,
restart, screen capture/input, model switch or Conversation test was attempted.
No new live Claude image turn or saved-session model inference was run.
No blanket acceptance for unsupported producer schemas, oversized screenshots,
or future model/runtime combinations.
