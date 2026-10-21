# Combined tiling and slim dock — blocked review

20 October 2026, worker-a7366. **Not accepted; production apply stays gated.**

## Latest consolidated result — read at event e14766

**Read, not rerun here:** browser reviewer worker-a7466's receipt c7475 on
this card, defect reproductions c7473 on the tiling owner's card, and completion
receipt c7477. The reviewer ran guarded hidden Edge on disposable copies.
Its source/report commit is `ebe9a91`, pending landing when read;
`research/window-lab/combined-review/REVIEW.md` is its detailed report.
This checkout remains `8f9ece9`; none of that source or evidence was imported.

Two implementation failures prevent acceptance:

1. Carry leaves 804–41,136 characters selected. The next carry starts Chromium's
   native text drag and receives `pointercancel`. Reproduced twice; clearing
   selection in the driver lets it proceed, which does **not** prove normal use.
2. After dropping, old dividers and Fit tools retain their previous geometry
   for 406–1,000 ms (24/24 carries), intercepting the next press. The automated
   `partition_navigation` step fails at both sizes for this reason.

Both defects are already with the source owner; this acceptance card changes
no implementation. The owner must supply a revised checkpoint, followed by a
fresh guarded review that does not clear selection to conceal defect 1 and
checks consecutive gestures during the post-drop interval for defect 2.

| Journey | Browser reviewer's reported result |
|---|---|
| Geometry and guard | Actual CSS 2560×1440 and 1280×800, DPR 1.5; visible, no page overflow or errors; `alex: untouched` every run |
| Clicks, desk/local edges, dividers, focus, shelf/pin, cancellations, stale fence | Passed at both sizes **with selection cleared before each press**; 12 desk-edge drops, 4 local edges and centre tabs, preview/result within 1 CSS px |
| Bare app and dock | Compact headerless app/appgrip; dock preview, duplicate prevention, reorder, remove/restore, hover names and open markers passed |
| Persistence | Reload identity and focused weights passed |
| Fit, extent handle, unsent draft/caret | Passed at 2560; at 1280 Fit/handle bounded by 300px allocation, composer cut off also in the unstaged world |
| Colours | Blocked: no pins have `tint=`; JEFF apply step 4 outstanding |
| Other coverage | Not run: touch pointercancel, workspace switch, document/view/window pins, changing receiver mid-carry, drops from tabs/focus; media controls out of scope |
| New viewer tabs | Landed `3cc2796` and staged viewer passages were not composed; no combined acceptance |

Reviewer evidence directories under `demos/combined-review/`:
`2026-10-20-180513-2560x1440` and `2026-10-20-181014-1280x800`
(shots and report.md). These paths are from the reviewer's receipt, not files
opened in this checkout. Its setup composed the owner's 57 files over main
`c3ad04e`, with four additive conflict unions and recorded hashes; partition-ui
matched checkpoint c7426. Its harness added Edge occlusion/backgrounding flags
after display sleep blanked the hidden page.

**Ran on this resume:** read-only git status, log and diff; tracked diff empty
before this report update. No browser retry, overlay, source fix, live apply,
host restart, media/account action or Conversation send. The card expressly
forbids repeating this runtime's known failed browser attempt. Acceptance
remains rejected; passing subsets do not clear either defect.

The following sections preserve this reviewer's earlier blocked attempt.

**Read:** main `8f9ece9`, landed dock `16ac2bf`, tiling checkpoint and JEFF's
integration requirement, staged navigation/apply acceptance, dock handoff and
`partition_hook.py` staged diff, both review-copy recipes, screen/guard lifecycle.
No source was changed. The tiling owner was contacted directly on its card.
At the first attempt the checkpoint did not confirm the external CarryTargets
hook. That source gate is now confirmed below; this review worktree still does
not contain the unlanded partition implementation.
Neither recipe's automated subset would constitute full acceptance.

## Updated handoff, 20 October

**Read, not rerun here:** the source owner's checkpoint c7426 confirms the exact
five-anchor dock/partition integration in the preserved tiling worktree, base
`c5c988c`, with partition-ui SHA256
`89769A67AFFAF5FA4783FB1F318E5BEA233AFFC6D10EC557174A7AFDC904E332`.
JEFF confirms that acceptance input in c7434. The refreshed review recipe
preflights both world halves before any write and preserves installed dock
definitions. Its automation remains PARTIAL; every journey below still needs
guarded browser execution. No source/worktree was copied or changed by this review.

**Read another worker's ran receipt, c7454:** the harness worker reports successful
hidden-desktop runs from a Claude lane: actual CSS pages 2560×1440 and 1280×800,
both DPR 1.5, clean guards and owned desktops removed. A card-click check passed;
its scrollnote check failed on a world fixture. These prove that lane's harness
capability, not combined tiling/dock acceptance. The precise reason Edge fails
under the Codex sandbox token remains untested. No bypass is authorised.

Harness fixes are reported in commit `bf9fb13`, on a commission currently ready:
CSS viewport sizing and startup-failure cleanup. They are not in this review
checkout (`8f9ece9`). The incoming reviewer must receive those fixes together
with the preserved integrated tiling source through the house; this reviewer
does not edit the source owner's worktree. JEFF's c7458 now requests that the
demonstrated browser-capable harness worker continue combined acceptance after
its source lands, without editing another worker's tree. This is a capability
requirement for this review, not a provider-wide queue policy.

The copied-world recipe remains in `research/window-lab/hud-dividers/review_copy.py`
with separate normal and `--small` runs. Full journeys are in the staged
navigation acceptance note and the source owner's NAVIGATION.md. No retry was
made in this Codex sandbox after the capability receipt.

**Ran once**, pinned interpreter, disposable world, no staging or input:

```
C:/Projects/Agora4/.venv/Scripts/python.exe research/text-desk-lab/notation/screen.py frontier-try --as worker-a7366 --lens home-base --visible --size 2560x1440 js "[innerWidth,innerHeight,devicePixelRatio]" facts home 1
```

Exit 1: `screen.py:283` → `sandbox_window.open_edge:563` →
`c.js("document.readyState")`: `ConnectionResetError [WinError 10054]`,
then `websockets.exceptions.ConnectionClosedError: no close frame received or sent`.
Failed before page-ready, viewport evaluation, facts or interaction.
No bypass, alternative browser launch or repeat at the smaller size.

In the source used for this attempt, open-edge failed before screen.run's cleanup `try/finally`.
Checked only this worktree's fresh sandbox state; it named screen-70032.
Ran its documented off switch, no broad process cleanup:

```
C:/Projects/Agora4/.venv/Scripts/python.exe research/window-lab/sandbox_window.py close --name screen-70032
```

Exit 0: **`closed sandbox screen-70032: its desktop is gone`** and
**`alex: untouched`**. That last verdict covers the cleanup command, not a
completed guard verdict for the failed acceptance run.

## Earlier attempt's journey results (superseded by the receipt above)

| Requested journey | Actual result |
|---|---|
| 2560×1440 at native 150%: CSS viewport, DPR, guard | Blocked before evaluation; requested size only, actual geometry/DPR unknown; no completed run verdict |
| 1280×800 | Not run after capability failure |
| Stationary/control clicks versus drag threshold; whole-panel ghost | Blocked, no gestures run |
| Four local/global edges, desk bottom half, preview/drop agreement | Browser blocked; source integration now confirmed separately |
| Every divider, both directions, minimum sizes | Blocked |
| Bare content-sized Spotify; safe control input | Blocked; no media/account action |
| Tabs, fill, pin, shelf, title, cancel, stale fences | Blocked |
| Dock pin panel/document/view; duplicate drops; reorder | Blocked |
| Deliberate remove, undo, restore; current workspace; open markers | Blocked |
| Compact colours, hover names, overflow/dock collision | Blocked; no facts/shots |
| Persistence/reload | Blocked |
| Unsent draft, caret and explicit chat context continuity | Blocked; no typing or Conversation send |

That earlier attempt established zero journey passes or implementation failures. No stand-in test
was substituted for browser acceptance. No screenshots, demo or visual claims.
No live world apply, HUD launch/restart, external app or real account operation.

**Earlier handoff:** JEFF requested continuation by the demonstrated browser-capable worker with
the harness fixes and confirmed integrated source. Use fresh copy-only staging,
record actual CSS viewport/DPR and full guard verdict at both sizes, and execute
every journey above. Existing partial recipes are starting points.
This review is parked; no further model/capability polling here.
