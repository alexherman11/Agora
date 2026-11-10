# Kernel builders and desktop repairs — 27 October 2026

Coordinator implementation and activation record. Current world: kernel8810. This is not the old Frontier integration plan.

## Delivered

**Ran:** House claimed Writing import and started a real ChatGPT-authenticated Codex turn, session `01a17f71-3ab3-7c13-93d2-8d9e362b4469`. Its first turn produced source and a 216-document manifest. A completed turn is **received**, not reviewed, landed or task-done. Owner corrections resume the same session, worktree and claim. Public progress now shows actual turn start, text and tool names; reasoning and raw tool arguments are excluded. Capacity is two builders. An obsolete pre-thread WM request was released, not duplicated.

**Ran:** House-only activation preserved JEFF's session and cursor. Existing authentication and module grants were reused. No paid fallback, credential, security setting or provider change was made. Committed implementation: `fe564da9f`, runtime-record compatibility `e1b47a34b`, actual-progress/asynchronous-retry repair `8f7f89bcf`.

**Ran:** dock component and both bar widget code hashes match committed source `26e247f52`; component review completed, lens arrangements and grants stayed unchanged. Window host and WM source `a0aabf673` were activated via normal off/undo, then fresh `wm.mode live`. All 14 world window records survived; 12 were eligible native windows before opening Lines (wallpaper and inactive widget records are intentionally excluded). Conversation and draft hashes stayed unchanged. Kernel and House were not restarted during native activation.

**Ran:** real `window.open lines`, `window.open seabright-map`, `window.open jeff-chat` calls were accepted. The loaded native host showed all three as normal windows together, with final pairwise nonoverlapping rectangles. Draft remained unchanged. No user app was quit. The narrow stale-cache close/reopen repair is loaded. Physical dock/top-right clicks were not automated; hidden component tests cover those routes. Repeated real close/reopen was not forced on Alex's working windows.

## Evidence and limits

- **Ran by repair workers, read by coordinator:** WM 62 tests in 26.553s, 60,000 invariant events, hidden native counts 1/2/3/4 and repeated restore four; input desktop unchanged. Packing is bounded and displacement memory session-local. Actual Spotify/Claude sequence and tactile quality are not certified.
- **Ran by repair workers, read by coordinator:** combined window/dock/JEFF/desktop suite 34 tests in 64.876s, OK; dock-specific 2 tests in 9.772s, OK; earlier shell 9 tests in 15.077s, OK. These are overlapping suites, not additive unique counts.
- **Ran by coordinator:** latest House/progress/record suite 32 passed in 3.66s; earlier runtime/adapter regression 68 passed. Private lifecycle fixtures prove claim, worktree, review/publication fences and retained state, not real writing import.
- Activation helper's first widget check mistakenly used `look` (which omits code). Reconciled using `rows widget`; top bar already matched, only dock needed its update. No unknown operation was replayed.
- Native activation readiness initially counted wallpaper and inactive widgets as real windows. Reconciled against eligible native rows; host restart had succeeded. Continued the retained WM off receipt rather than repeating window restart.

Machine-readable activation evidence: `evidence/activation-20261027.json`. Detailed repair handoffs: `src/desktop/agora-wm/ADAPTIVE-20261027.md`, `src/desktop/kernel-desktop/LINES-DOCK-REPAIR-20261027.md`, `src/desktop/kernel-desktop/JEFF-CHAT-DIAGNOSIS-20261027.md`.

## Shared ownership and outstanding work

Existing Board cards, all read back: launcher `dk970`; WM `dk966`; Lines/Map `dk976`; JEFF `dk992`; Writing `dk954`. The three repairs are activated with exact evidence. External repair owners released their files before integration. The current in-world Writing builder remains the sole writer of its task tree. One independent helper performed read-only review.

**Writing is not imported.** First worker printed `Ran 7 tests`, `OK (skipped=1)`—six passing checks. Correct manifest count from independent metadata review is 200 verbatim documentation notes, 14 generated shelf indexes and two personal documents. Independent review found missing represented-principal validation, external URLs incorrectly resolving locally, generated-index attribution and insufficient second-principal privacy testing. These are returned to the same builder for source-only corrections. Current documents and frozen archive are untouched.

**Denied, known not completed:** real-kernel fixture creation at `C:/Users/Alex/AppData/Local/Temp/writing-import-thuqm2pq/log` (WinError 5), plus cleanup; Git staging/commit at `C:/Projects/Agora4/.git/worktrees/kernel-dk954-d521ff68e0/index.lock` (permission denied). No retry, alternate path, permission change or host-side proxy commit occurred. There is no pending approval UI receipt known to this coordinator. These exact actions require supported resolution with new relevant authorization before independent kernel proof, commit, normal House review/landing and reviewed live import. The CLI's MCP environment was absent; no new credential was invented.

Useful source changes are preserved in `.worktrees/kernel-dk954-d521ff68e0`; read its `BUILD-RESULT.md` for the latest result. Source correction is permitted independently of the denied operations, whose holds remain explicit. Do not treat a worker ending or an activated desktop repair as completion of the separate Writing task.


## Final source review, 22:48 UTC

**Ran by the in-world builder, read by coordinator/reviewer:** `Ran 10 tests in 1.652s`, `OK`, explicit non-kernel checks. The same Codex session has completed three turns and is received/held; no active in-world builder remains. The five Writing files remain uncommitted in the existing House tree.

**Read independently:** principal validation, external-link handling, manifest-bound review, generated-index attribution, shared-document provenance and the valid-second-principal test source now address the findings. No additional material issue was found in the reviewed write path. The read-only CLI `plan` does not use the principal guard; do not interpret the handoff's broader wording as proof of that. No real-kernel privacy/integration or live import proof exists yet.

**Restore-memory boundary:** unit/state-machine tests cover exact, nested/out-of-order, constrained and manual-override restoration. The hidden native proof verifies successive four-window visibility and repeated restore, not native opener-close restoration. The live check verifies Lines/Map/JEFF visibility and nonoverlap, not the Spotify/chat/Claude sequence or close-memory feel. No stronger claim is made.

**Specific next approval:** one supported escalated run of `ImportProof.test_real_kernel_import_visibility_provenance_and_rerun`, including isolated `writing-import-*` Temp fixture creation/write/cleanup; and `git add`/`git commit` for only the five reviewed files in `.worktrees/kernel-dk954-d521ff68e0`, using its existing shared Git index/object database. Do not change ACLs, sandbox policy, credentials or security settings. After those pass, use normal House review/landing and existing local activation authority. These are known denied/uncompleted actions, not a pending tool approval or uncertain live import.
