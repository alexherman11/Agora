# Combined tiling + slim dock: guarded browser review (a7466, for a7366)

worker-a7466 (builder-1), 20 Oct 2026. Acceptance only: no source fix to the reviewed code, no live apply.

## Round 5 (c7532): JEFF's staged glance fix a7531, and the Board header press

**Bytes (ran):**
- Source unchanged since c7517: partition-ui.js 2F294196…, lens.js 5915058E… (composed with main's one line).
- The owner has since changed two test files:
  - partition_navigation.py E09828CB00D7267198A1A8BF407A18EEFB63327B4FCA792801384ADADC929F4C
  - test_navigation_step.py B88EA3355398E3294DB71FBD05B9DF4C727AC4505E734DD727FFF7632F83CFE5
- Composed copy-only over c429747: 58 files, 0 conflicts; restored afterwards. World copy at e14981 (later runs at e15270). DPR 1.5 at both sizes.
- The guard verdict was "untouched by the sandbox" on every run. One run (`213308`) also logged a foreground change on Alex's PC with no input, not to a sandbox window.

**The staged fix, applied only in the copy** (`journeys.py --glance-fix`): exactly a7531. Add `token glanceclear = #00000000` and append `, edge glanceclear` to `role lgstat`; `lgstat.on` is unchanged. The desk answered `ok replace a5206`.

**Measured first, without the fix** (`demos/combined-review/2026-10-20-213037-1280x800/focusdiag.json`, "count chips"):
- In focus, two of the three glance counts ("7 wait on you" and "1 queued") wear `lgstat.on`. That gives them a 0.667 px solid ink border (1 device px), so each is 36.8 tall against 35.5 for `lgstat`.
- Out of focus, all three are `lgstat`: 0 px border, 35.5 tall.
- Two chips at 1.3 px each give the 2.7 px top-row change.

**With the fix** (`213146` and `214036` at 1280; `213308` at 2560):
- Every chip is 36.8 tall, with a 0.667 px border in both states: transparent when off, ink when on. Widths are the same in both states.
- The top row holds at 298.4 at every stage, and the root at [16, 330.4, 1248, 378.8].
- Focus exit, Board in focus, Chat carried to the bottom: preview = right after release = after the answer = [16, 527.9, 1248, 181.5]. Difference [0, 0, 0, 0], root spread 0.0, at both sizes. tabs-focus passes at 1280.
- **The drift is closed.**
- Side effect: the top row now always reserves the border, so at 1280 the panels are 379 tall instead of 383 (3 chips × 1.33 px). No count state shifts against another.

**Full regression with the fix:**
- 2560 (`213308`): every journey passes except the new `countpress` (below); dock-colour is blocked (no tints).
- 1280 (`214036`): passes include focusdiag, tabs-focus, busy, consecutive, consecutive-paced, immediate, refusal, cancel, containment, receivers and dock. Fails as before: fit (n/a by the 300 px allocation), draft and composer (composer cut off), doc-pins (viewer title under `DIV.r-top`). Plus `countpress`.

**The owner's updated recipe (`partition_navigation`, E09828CB…) — PASS at both sizes** (`hud-playtest/2026-10-20-214748` at 1280, `214813` at 2560).
- It now logs pointer events with their ancestry: every press is on `a5676/appgrip`, `prevented: false`, `selected: 0`.
- Marked slow at 462 / 508 ms.

**The Board header press, made deterministic (new journey `countpress`)** (`213037` and `214036` at 1280, `213308` at 2560; ancestry in `countpress.json`):
- After the Board is carried to the bottom, the journey presses every text piece inside its title grip `a5674/grip` (`div.r-panehead data-carry`, user-select auto). Each press moves out and back to its start; there is no Escape and no selection clearing.
- `The board` (`title < div.r-panetitle`): carries.
- `7 need you` (`you < div.r-nbsmall_need / lens:home-board-small < div.r-nbsmall / sum < div.r-panesum / grip`), `1 moving` (`moving < div.r-summary / …`) and `1 wait on JEFF` (`waits < div.r-nbsmall_jeff / …`): not controls, and inside the grip. At 1280 each press starts a text selection that runs into the Board body. At 2560, `7 need you` selected 1 character and the other two did nothing; none of them carried.
- `◆` (pin) and `–` (away) are controls: a press and drag on them does not carry, but at 1280 it selected text (" working").
- The question for the owner: the summary is a nested lens (`home-board-small`) inside the grip. If it is meant to be grip interior, it should carry. If it is excluded, it should still not start a page selection. A drag from a control should not select either.

**Bytes reviewed (ran; all five match c7517):**
- lens.js 5915058E0E1A0C7266EB9048AB1E786D58ACC61F95B78986806E2971AB435230. Composed by a three-way merge with main 5837d3e: one line differs from the owner's file (main's `if (p.remember) el.dataset.remember = p.remember;`).
- partition-ui.js 2F29419624DD1691E13D8FFC55D9B38B8B5BDC1BDEAF64D510C253C7A7BB129A
- test_partition_ui.js F8C5D716E80889AB63A8292A9709E94835A41BD7ABE8947AF765703F9CACDE43
- partition_navigation.py 07066CC9C79F7F8DF603D7D3E241EF210E8F72E5BF8BF8040C89DE58D3C2466C
- test_navigation_step.py 2576A48037A50E2754D9516A0B8697AA8C02D53FBDD7DD1A767FC912E4E0318E

Composed copy-only over 5837d3e: 58 files, 4 block unions, 0 conflicts; restored afterwards. World copy at e14924. DPR 1.5 at both sizes. Guard verdict on every run: "alex: untouched by the sandbox".

**Focus exit, Board in focus, Chat carried to the bottom — still fails at 1280; passes at 2560 (ran).**
- 1280 (`demos/combined-review/2026-10-20-193432-1280x800`, `193525`):
  - the partition root is [16, 329.1, 1248, 380.1] at focus, pickup, preview and release, and [16, 326.4, 1248, 382.8] after the answer;
  - the top row is 297.1 tall at focus, pickup, preview and release, and 294.4 after the answer;
  - preview minus result [0, -1.2, 0, +1.5], unchanged from round 3.
- The containment holds the partition (`contain: size layout`, measured), but the drift comes from outside it: the top row `f5664/top` lies outside the partition, and inside it `widgets/a6348` (the clock-and-counts widget) is 244.6 px tall in focus and 241.9 after. The capture is in focusdiag.json, "top row parts that changed".
- 2560: the root height spread across the stages is 0.0 and the difference is 0.
- No tolerance was widened.

**Containment (new journey `containment`) — PASS at both sizes (ran).**
- The root is whole: [16, 326.4, 1248, 382.8] at 1280 and [16, 79.8, 2528, 1269.3] at 2560, equal to the frame before.
- Every panel is inside the root, none cut sideways, none empty; the same holds in focus and after focus.
- 0 fixed-position descendants inside the root. Wheel scroll inside a panel moved it 0 to 200.
- Not covered: a part menu inside the partition. No `[data-menu]` part was found there; part menus are added to body, so containment cannot place them (read lens.js:489-504).
- Floats are lifted into the top layer (read lens.js:351-366); they were not driven.

**partition_navigation (the owner's corrected recipe), owner bytes, no probe — PASS (functional) at both sizes (ran).**
- 2560: `demos/hud-playtest/2026-10-20-193557`. 1280: `193623` and `193648`.
- "title click unchanged; four global edge spans; one divider persisted; copy fixture restored". Marked slow at 513-542 ms against the 300 ms aim.
- Every logged carry hit is the panel's appgrip (`.../a5676/appgrip`, 8 px tall).
- This was 0 of 6 at 1280 in round 3.

**Full regression:**
- **2560** (`193712`, `195230`): every journey passes in `195230`, with dock-colour blocked (no tints in this world; the tints journey passes). Passes include busy, consecutive, immediate, refusal, cancel, cancel-policy, draft (caret 16), composer (context unchanged), receivers, dock pins/order/look, doc-pins and the workspace emulation.
- **2560, one failure in five runs of `consecutive-paced`** (`193712`): after the first carry's answer, the next press on the Board's title selected 818 characters and did not carry. The shot shows the selection inside the Board's header text "1 wait on JEFF", a count that was in the header in that copy. Reruns (`194436`, `194505`, `195230`) passed. The press diagnosis (element under the press) was added afterwards and has not caught a failing run.
- **1280** (`194552`): the same as round 3. Fails:
  - focusdiag and tabs-focus: the focus drift above;
  - fit: the 300 px allocation bounds it, n/a by design;
  - draft: typing did not arrive, and composer is blocked; both because the composer is cut off at 1280 (`BODY.r-desk` under its centre), as before;
  - doc-pins: the viewer title is under `DIV.r-top`, as before.
  - Everything else passes, including busy, consecutive, immediate, refusal, cancel, containment and receivers.

## Round 3 (c7505): the owner's repair c7502

**Bytes reviewed (ran, all match c7502):**
- partition-ui.js 59313EC1C0A6774362B60A4208530467FD89CD4FD6FB6DE30AC803CB4FEDDAE6
- test_partition_ui.js 40D80DC066B36FADB0BA7CC1400525198CB52B6D8423194EC04CCB39194A4BBC
- partition_navigation.py 11568A7DD155DF755441032A160AE6DE35FB9AD84437CA50CBDA93AE41C912C6
- test_navigation_step.py A4B0F26797A0DEF4E9476C54E776D8B5AAC67E6ED0963716CB523BB8CBCED0E7

Composed copy-only over main fda965e: 58 files, the same 4 block unions, 0 conflicts. Restored afterwards.
Every run's guard verdict: "alex: untouched by the sandbox". DPR 1.5 at both sizes. The world copy was at e14869.

**Busy press (new journey `busy`) — PASS at both sizes (ran).**
- Setup: answer delayed 1500 ms. Drop the Board at the bottom, then grab again at once.
- Result: declined cleanly. No ghost, 0 characters selected, userSelect unchanged, only a pointerdown event, layout held.
- The answer then painted after 594 / 703 ms (1280) and 609 ms (2560).
- The next carry after the answer landed at its preview, e.g. [16, 326.4, 480, 383] at 1280.
- No selection workaround is used: leftover selection is only counted.

**consecutive / consecutive-paced / cancel — PASS at both sizes.** Example: 2 carried, 1 declined cleanly.

**Full regression runs** (shots and facts in `demos/combined-review/`):
- `2026-10-20-190202-2560x1440`: every journey passes. dock-colour is blocked because this world has no tints; the tints journey passes.
- `2026-10-20-190856-1280x800`: every journey passes except:
  - focusdiag and tabs-focus: the focus mismatch below;
  - fit: n/a by design (bounded by the 300 px allocation);
  - draft and composer: blocked, the composer is cut off at 1280 (pre-existing);
  - doc-pins document: blocked, the viewer scrolls its title out of reach.

**Remaining product defect: focus-exit preview at 1280** (ran, `demos/combined-review/2026-10-20-191538-1280x800/focusdiag.json`).
- Carry Chat to the bottom edge while the Board is in focus:
  - preview [16, 527.1, 1248, 182], which equals the rect right after release;
  - after the answer [16, 525.9, 1248, 183.5];
  - difference [0, -1.2, 0, +1.5].
- The trees are identical. `P.plan` got bounds {w: 1248, h: 380}: the partition root in focus is client 1248x380 at y 329.1.
- After focus exits, `P.geometry` gets h 383 (root 1248x382.8 at y 326.4).
- Cause: the layout's top row (`f5664/top`) is 297.1 px tall in focus and 294.4 px after. So the preview is planned in a frame 2.7 px shorter than the one it lands in.
- Plan options: minimum [240, 140], gap 16, visible [a5676, a5674, a6799, a6802], intrinsic {a5676: [401.25, 179.5]}. Split minimums after the answer: [140, 140].
- At 2560 the top row does not change, so the difference is 0.
- No tolerance was widened.

**partition_navigation (the owner's corrected recipe) — not acceptable as a gate yet (ran).**
- **2560, owner bytes** (`demos/hud-playtest/2026-10-20-191614`): FAIL inside `restore_fixture`. Message: "copy navigation fixture restore refused: ERR stale: f5664 changed since you last saw it (e14878 prop by alex); look at it again before acting". All 3 read+prop attempts stayed stale, and because the error is raised in `finally` it hides the step's own result.
- **2560, with a review-only probe** (`read <layout> :3` replaced by `look <layout>`; not the owner's bytes; `2026-10-20-191700`): the restore succeeds and the step passes functionally: "title click unchanged; four global edge spans; one divider persisted; copy fixture restored". It is marked slow at 482 ms. So `read` does not refresh the fence, and `look` does.
- **1280, probe on, 6 runs** (`191835`, `191912`, `191946`, `192018`, `192054`, `192124`): every run failed, at different points:
  - right edge drop, twice. In `192018`: before the drag, nothing was sending and 0 characters were selected. The press was at (256, 330.4), 4 px below the carried panel's top (panel [16, 326.4, 480, 383]), and was dragged to (1262, 517.8). After it, 32637 characters were selected and there was no ghost. The press started a text selection instead of a carry. Whether that point is outside the title (a test defect) or inside it (a product defect) was not captured; the hit-test probe ran only on runs that failed elsewhere.
  - top edge drop, once (`191912`).
  - divider, three times (`191946`, `192054`, `192124`): "refused: f5664 already has that". The 40 px divider drag produced the same weights at 1280.

**Bytes reviewed:** partition-ui.js 2CD497F27AE22C621CB7B4140BC938564E7293178563DF0878F30ADA6168B535 and
test_partition_ui.js 44D7F9040B7E36235FC1F867DC216AFC02060869305B0D5ADAEF97E073744749. Both match c7487.

**Setup:** recomposed by the landed overlay.py over main a981e1a: 57 files, the same 4 block-only unions, 0 new
conflicts. The disposable copy was staged by review_copy.stage_copy with no refusals.

**Driver:**
- Round 1's selection-clearing workaround is **removed**; leftover selection is only counted.
- A journey that starts with text left selected by the previous one runs on a reloaded page instead, and that is
  reported.

**Verdict: still not accepted. One residual defect, plus one small geometry miss at 1280x800.**

1. **Both round-1 defects are fixed when carries wait for the world's answer.**
   - Every carry ran with nothing selected and body userSelect `none`; release and all 6 cancel routes put the
     prior policy back, including an inline `text`.
   - After each release, old dividers and Fit tools were gone within 15–47 ms, which is just the first poll (round
     1: 406–1,000 ms).
   - With the answer held back 1.5 s, no obsolete tool stood, the spots where old dividers had been hit panel
     content, and the optimistic layout held.
   - A refused drop rolled back, with the dividers back and the refusal said.
2. **Residual: a carry started while the previous drop's answer is still pending is declined, and its drag selects
   page text.**
   - The pending window is 422–610 ms on this copy.
   - `carry()` owns the press but returns busy without suppressing selection, so the drag selects text (818
     characters); then the press after that, landing on the selection, is cancelled by Chromium's text drag.
   - Reproduce: drag the Board title to the bottom edge, release, and grab it again at once. No ghost appears, and
     text is selected. The `consecutive` journey failed this way at both sizes; `consecutive-paced` (waiting for the
     answer) passed at both.
   - The same thing left 7–27 characters behind in `immediate` (its declined second carry). That is why the next
     journey ran on a reloaded page.
   - Suggested scope, for the owner: a declined press should still suppress selection (or the carry should
     queue).
3. **Minor, 1280x800 only: a drop from focus mode misses its preview by 1.2–1.5 px.** Preview
   [16, 527.1, 1248, 182], result [16, 525.9, 1248, 183.5]. At 2560x1440 the two agree exactly.

**Newly covered c7475 cases (ran):**

| journey | 2560x1440 | 1280x800 |
|---|---|---|
| consecutive carries, paced by the world's answer | pass | pass |
| consecutive carries with no wait | **fail** (residual 2) | **fail** |
| answer held back 1.5 s: no obsolete tools, optimistic layout, answer restores tools | pass | pass |
| refused drop rolls back | pass | pass |
| Escape, resize and blur restore the selection policy (prior '' and 'text') | pass | pass |
| composer: words, selected range 3–9, attach item and To row through two drops and a divider | pass | blocked (composer cut off, pre-existing) |
| drop from a tab group / from focus mode | pass | **fail** (focus drop off by 1.5 px) |
| dock changed while held / carried panel changed while held: no pin, no commit, no split fallback | pass | pass |
| pin a surface and a document by the viewer title; the window-definition pin's "Open as a window" asks the host | pass | surface pass; document blocked (the viewer scrolled its own chips and title out of reach in a 383 px panel) |
| staged tints applied in the copy | pass: purple, amber, green, and blue (blue has no role in home-dock, so it draws the default blue) | pass |
| workspace identity, EMULATED by replacing the layout with its own copy (no workspace exists in the world) | pass: typed refs remapped, same geometry, the pin opened the copy's own panel | pass |
| all round-1 journeys (edges, local, dividers, focus, shelf, stale, bare, dock…) | pass, no workaround | pass (Fit bounded by allocation; draft blocked as before) |

**a7045's recipe step:** `partition_navigation` no longer fails on an old divider, but it fails on its own test
logic.
- Normal size: the "top" check is the same "spans the width" test as "bottom", so it was already true and the
  harness refused to time it.
- Small: the fixture restore did `look` then `prop`, the page's own commit landed in between, and the prop was
  refused as stale. That hides whatever happened first.
- Both are test defects for the owner, not product defects.

**Not run:**
- Real touch `pointercancel`.
- A real workspace switch (a6427's world half was never applied).
- A drag-created window-definition pin (there is no drag source for one).
- Media controls.
- Tabs 3cc2796 with a7439/a7441, left separate.

**Guard:** "alex: untouched" on every run. Page errors: none.

**Reports:** demos/combined-review/2026-10-20-183512-2560x1440, 2026-10-20-184201-1280x800, and composer
2026-10-20-185103-2560x1440. Recipe runs: demos/hud-playtest/2026-10-20-184854 and 184921.

## Round 1 verdict (superseded above)

Not accepted yet: two defects for the source owner (a7045), both reproduced in the real hidden Edge. Everything else
I could drive passed at both sizes. Production apply stays gated.

1. **A panel carry selects page text, and that kills the next carry.** The partition carry (partition-ui.js `carry`)
   never turns off text selection; lens.js's older carry does (`document.body.style.userSelect = "none";
   getSelection().removeAllRanges()`, lens.js:1268). Mid-carry 804 characters were selected at 2560x1440, up to
   41,136 depending on the path. The next press that lands on that selection starts Chromium's own text drag. The page
   gets `pointerdown`, `mousedown`, then `pointercancel` straight away, and no carry starts: no ghost and no
   preview, so the panel does not move. The press clears the selection, so the carry after that works.
   Reproduce: drag any panel title to the desk's bottom edge and release, then drag the same title again.
   (syncdiag, ran: carried, then not carried with 804 characters left selected, then carried with the selection
   cleared first, twice.)
2. **Old dividers and Fit tools stay in place for about half a second after a drop.** `finish()` paints the
   planned layout with `tools=false`, so the 12 px invisible dividers and the Fit buttons keep the old geometry
   until the world's answer re-syncs. Measured from release until gone: 406–1,000 ms at 2560x1440 and
   422–922 ms at 1280x800 (24 carries each). A press in that window lands on an old divider. That is exactly why
   a7045's own `partition_navigation` step failed at both sizes ("a press at its centre lands on DIV").

Pre-existing, not from this change: at 1280x800 the chat composer can't be reached. The top widgets stack to about
326 CSS px, the panels get 383 px, and the composer sits below the chat panel's cut. The unstaged world behaves
the same (screen.py, ran: the composer's centre is covered).

## Setup (copy-only) and hashes

- Source: a7045's 57 uncommitted files on base c5c988c, composed over main c3ad04e (landed harness, tabs
  3cc2796) in this worktree's files only, by `overlay.py`. a7045's tree, git and the live world were not
  written. Result: 49 clean (new, theirs, merged or same as main) and 4 conflicts, all additive unions recorded in
  `resolved/`:
  - lens.html: both script lists
  - scene.py: PAINT_WORDS `remember` beside partition's words
  - lens_ir.py: `_static` words, the same union
  - FRICTION.md: main's version kept
- `manifest.json` lists every file with base, theirs, main and composed SHA-256. partition-ui.js is
  89769A67AFFAF5FA4783FB1F318E5BEA233AFFC6D10EC557174A7AFDC904E332, the same as c7426.
- World: hud_playtest's disposable copy of frontier-try (the copy was at e14709), staged by a7045's
  `review_copy.stage_copy`. That preflights both halves and then makes one write at a time; there were no
  refusals.
- Harness delta, my own a7413 area, committed: Edge now starts with
  `--disable-features=CalculateNativeWinOcclusion --disable-backgrounding-occluded-windows
  --disable-renderer-backgrounding`.
  - Why: with Alex's PC idle for 39 minutes (display probably asleep), the hidden page went
    `visibilityState: hidden`, drew blank and dropped carries.
  - With the flags (ran): visible and drawing. Isolation is unchanged.
  - The driver also marks any journey that saw a hidden page as invalid.
- Composed tree tests: test_review_copy 8 ok, test_dock_integration 2 ok, test_navigation 10 ok,
  test_scene 58 passed. The node DOM tests were not run (node needs approval here).

## Journeys (ran: journeys.py, hidden Edge, guard on)

Pages measured: **2560x1440 CSS at DPR 1.5** (fullscreen on its hidden desktop) and **1280x800 CSS at DPR 1.5**.
Both visible, no page overflow, page errors [] in both runs. Guard on every run: "alex: untouched by the sandbox".

The driver clears any text left selected before each press (defect 1) and reports each count. Without that, about
half the carries fail.

| journey | 2560x1440 | 1280x800 |
|---|---|---|
| facts: CSS size, DPR, no overlap/overflow/dock collision/stale chrome at rest | pass | pass |
| title click, 4 px move and text click on all four panels: no snap or resize | pass | pass |
| whole-panel ghost past 5 px, source dims to .35, preview, no animation, Escape cancels | **fail** (selection, defect 1); rest pass | **fail** (467 characters); rest pass |
| four desk edges × Board, Chat and bare Music (12): preview = result within 1 px, full span | 12 pass | 12 pass |
| four local edges + centre tabs on the Viewer; each tab selects its panel | 5 pass | 5 pass |
| Fit content / ↔ restore; bare app content-width handle kept over reload | pass | no change: both already fill their 300 px allocation, which the design says bounds them |
| every column divider, then with Chat across the bottom every divider: ±80 saved, both ends hold minima | pass | pass |
| double-click focus: pinned Chat beside, rail; focused divider kept over reload; double-click restores | pass | pass |
| pin the Board panel to the dock, shelve it from the header, open its pin twice: one panel, same place, open marker right | pass | pass |
| resize and blur events mid-carry cancel with nothing committed | pass (dispatched events) | pass |
| competing tree change while held: the stale drop is refused and the page repaints | pass | pass |
| unsent chat draft and caret through drop, divider and focus; words kept over reload | pass (caret at the end after reload) | blocked: composer cut off (pre-existing) |
| bare Spotify: compact, no generic header or Fit; appgrip carries the whole app | pass | pass |
| over the dock only the dock's box shows, back over the desk only the split's; two drops make one pin; tree untouched | pass | pass |
| reorder pins both ways and to the end; outside drop changes nothing; Remove pin; Restore removed pins | pass | pass |
| hover names readable (15 px, inside the page); open markers true | pass | pass |
| pins coloured apart | blocked: no pin has `tint=` (live dock checked too); JEFF sets tints at apply (handoff step 4) | blocked |
| changed layout identical after reload | pass | pass |
| a7045 recipe `partition_navigation` | fail (defect 2) | fail (defect 2) |

Reports and shots: `research/window-lab/demos/combined-review/2026-10-20-180513-2560x1440/` and
`2026-10-20-181014-1280x800/` (report.md, report.json, numbered PNGs) in the main checkout. Recipe runs:
`demos/hud-playtest/2026-10-20-173108` and `2026-10-20-181541`.

## Not covered

- Real `pointercancel` (touch).
- Workspace switch with dock reopen.
- Pinning a document, surface or lens by the viewer title, or a window definition.
- A receiver changing while a panel is held over the dock.
- Drops started from a tab or from focused mode.
- Music playback and heart controls: nothing is playing in the copy, and media/account operations are out of
  scope, so Connect Spotify was never pressed.
- Landed tabs (3cc2796) plus staged a7439/a7441: not composed here. That stays a separate acceptance, so no
  dependency drift is hidden.

## Withdrawn on the way

- "The carry after an Escape fails" was defect 1: the carry before the Escape had left text selected.
- Blank shots and dead carries around 17:40 were Edge's occlusion handling (see the harness delta), not the page.
