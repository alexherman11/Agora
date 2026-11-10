# a7925: deployed tiling, the running HUD's painter, and the drag stalls (21 Oct 2026, builder-2)

**Status:** acceptance and diagnosis only. No source was changed. Nothing ran on Alex's screen, nothing was restarted, and nothing was applied live.

## Does the running HUD have the partition painter?

**What the source says** (read: `deskd.py` `painter_version`, `/api/version`; `lens.js` `versionIs`, about line 1550):
- The door serves the live checkout's `desk-shell`.
- `/api/version` hashes every painter file on each request.
- An open page polls `/api/version` every 5 s. When the hash changes, it reloads itself with `reloadKeeping` (the view is kept) as soon as hands are free.
- Hands are busy while a composer has words in it, while typing, carrying or resizing, while a menu draft is open, or while image comments are busy. During that time the quiet line says "new screen code: it will load when your hands are free" and it asks again 5 s later.
- So a world compile never activates scripts, but a changed painter file does, by itself, when hands are free. No reload by hand is needed.

**What the live door says** (ran, read-only GET of `/api/version`):
- `{"code": "197f513", "painter": "f400707deea1", "shape": 1}`.
- `painter_hash.py` over the live checkout's desk-shell gives `f400707deea1`, so the door is serving main's painter.
- My worktree's copy hashes to `cbdea4c46456`. The only differences are CRLF line endings in 3 files: `shell.js`, `style/calm.style` and `checks/continuity/run.mjs`.
- `lens.js` contains the partition painter. It has been there since 28a55be, and `lens.js` changed again at 9ab1bb0, so every open page has been offered the newer painter since then.

**Not known:** which painter the running page actually holds. Nothing reports a page's painter back to the server, and Alex's screen was not looked at. Alex's m7972 report, that dragging between tiles stalls, is itself a sign that the partition painter is running.

**If JEFF needs it certain:** the supported path is to do nothing. The page loads the new painter by itself once hands are free. If its quiet line reads "it will load when your hands are free", an unsent draft or an open menu is holding it.
- Draft consequence (ran, draft journey at 2560): an unsent chat draft's words survive the reload; the caret does not.
- No command for Alex, no restart.

## Deployed identities (copy of live at e17475, run at e17553; live tree read-only)

- **home-tiling a5692:** 137 lines, SHA-256 `0678BAF96E0AEF4E02E2CFF1F8A00B84896439D70BC33C17E40AEF76896A8A7E`. Identical to builder-1's read at e16666, so it is unchanged since JEFF's e16658.
- **Alex's layout f5664:**
  - The tree has changed since JEFF's e16654, by Alex. Tree SHA-256 `313371F75A4984AFC4ABA8152E60AA029188650968A7182F47C761D63AAC6682`.
  - It is in focus on The board (`full=a5674`).
  - The copy's tree equals live: `do prop` with the live tree answered "already has that".
- **Panels:** 8 members. Music, The board, Viewer and Chat are out; Waiting on you, The house, The lowdown and On your screen are shelved. Chat is pinned. The tree was not reapplied or overwritten anywhere.

## Real browser: hidden desktop, guard every run "alex: untouched by the sandbox", DPR 1.5

| Journey | 2560x1440 | 1280x800 |
|---|---|---|
| facts | pass: Viewer 1271x1192, board 535x1192, Chat 570x1192 | pass, but panels **202 px tall**: Viewer 586x202, board 247x202, Chat 263x202 |
| ghost | pass | pass; the drop preview is 93 px tall |
| counts5 (5 presses on each count) | pass | pass |
| controls | pass | not run |
| cancelrelease | pass | pass |
| stale (fenced drop) | pass | pass |
| draft (no sends) | pass: words and caret kept through drop, divider and focus; words kept over reload | **fail: the chat composer is cut off, so typing never reached it** |
| focus | "fail" is the harness, not the HUD: Alex's layout starts focused, so the first double-click correctly un-focused it (shot 12-focus) | not run |
| dividers | columns pass. In rows: pushing an already-minimal divider shows raw text, "refused: f5664 already has that; props now: …" (cosmetic). "rows divider 2 vanished" is unexplained and not verified. | not run |

Report folders: `C:/Projects/Agora4/src/desktop/demos/combined-review/`
- `2026-10-21-113835-2560x1440-deployed`
- `2026-10-21-114241-1280x800-deployed`
- dragtimes: `…113611-2560x1440-deployed` and `…113722-1280x800-deployed`

### Concrete defect at 1280x800

The home base leaves the tiling about 200 px of an 800 px page:
- the clock and count band stacks its counts vertically, taking about 330 px;
- the dock and the shelf rail, which wraps into several rows, take about 200 px.

Every panel is cut:
- the board's cards are clipped;
- Chat shows its header but no reachable composer;
- the drop preview is 93 px.

This is authored layout, not the partition painter: it lives in the home base lens (top band, shelf rail) and the panel lenses (board, jeff-chat). The historic small-screen composer limit is now worse: the composer cannot be reached at all.

## Drag "refreshes/pauses" (c7983): measured with `dragtimes`

The page was instrumented with long-animation-frame attribution, fetch timing, rAF intervals and DOM mutations. Two gestures were measured: a slow carry of The board across every tile and back, and a column divider moved 200 px out and back. Each ran quiet, and "busy": one visible card change on the copy every 1.5 s, close to the live churn of about 100 events in 6 min.

**While held:** frames stay smooth (p95 16.8 ms) at both sizes, quiet and busy. The worst frames while held:
- 67 ms (2560, busy divider);
- 148 ms at 1280 at the pick-up, from `onpointerdown` in lens.js (116 ms) plus `move` in partition-ui.js (30 ms).

**The cost is the scene:**
- Every world change makes each poll (1.5 s) fetch a whole scene of about **1.7 MB**, with a **240–540 ms** round trip.
- Painting it is one long frame of **80–150 ms** (`Response.json.then` in lens.js, i.e. paintAnswer). About **41–61 ms** of that is forced style and layout.
- While a divider is held, answers are fetched but not painted (paintAnswer returns while resizing). They land together just after the release: 1–2 frames of 100–150 ms.
- With live-like churn this hitch repeats with each changed scene, not only when dragging.
- This matches the c7983 report as "pauses". I saw no reload or full blank repaint during any gesture.

**Other observations:**
- At 1280, busy: one stop of the slow carry showed no ghost. The cause is not established.
- After a carry, the "The board / Drag the title to move this panel" tooltip stays up, at both sizes.

**For a7987:** two targets.
- The full-scene size and full repaint per world change. The scene bodies are 1.7 MB for a home base.
- The pick-up press cost at small sizes.

Neither is the partition tree logic.

**Limits kept explicit:** completion after a release exceeds 300 ms whenever a scene answer is pending (240–540 ms round trip plus an 80–150 ms paint).

**Not checked:**
- the WebView2 HUD itself (only Edge on the hidden desktop, RTX 2080 Ti);
- Alex's real event rate;
- touch;
- dock, shelf and music journeys at 1280;
- the dividers row anomaly.
