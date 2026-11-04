# Current source handoff: dk1706 and dk2125

4 November 2026. Supersedes the operational instructions in
[the original activation report](FULLSCREEN-ACTIVATION-dk1706.md) and
[the policy-reload report](POLICY-RELOAD-dk1706.md) for this draft.
Those documents retain historical evidence, refusals and rejected designs.
This document grants no lifecycle, settings or security authority.

**Read:** dk1706 records landed/reviewed
`e959129ca405790c3240375754a2cb4c9a415768` and Alex's subsequent failed
fullscreen/Spotify outcome. dk2125 adds browser width, growth and guaranteed
requested-window visibility. JEFF's card facts are the live-state authority;
the worker did not inspect the live WM again.

**Read/source:** this uncommitted draft changes sharing behind the existing
`wm.arrange` / `wm.focus share=yes` / `wm.restore share=yes` words. Browser and
Electron windows have a ceil(work-area width / 2) floor; Spotify/Agora can
share the rest. Explicit bar requests re-probe learned movement failures.
Fullscreen state restoration precedes placement. Packing precedes LRU
eviction; neither the request nor a fullscreen participant is a fallback
victim. Closing shared participants grows remaining tiles. Failed fullscreen
geometry retains the app and gives the request a remembered-size foreground
plan, with a WM note. Fresh Agora opening arms the same share transaction.

**Unrun:** current deterministic tests, native checks and activation.
Pike explicitly assigned all test/fixture execution to independent House
review. See root `BUILD-RESULT.md` for each authored test and earlier denials.
Do not treat a source review, syntax check or generic House build as user
acceptance.

## House review and never-shown acceptance

1. Independently inspect this draft and its diff against the landed source;
   run the supplied pure-policy, controller, native-method seam and shipped
   dock-component contract checks under House-owned fixture admission. Use
   pinned `C:\Projects\Agora4\.venv\Scripts\python.exe`; do not ask the worker
   to retry its denied scratch folders or locks. The controller native
   acknowledgements and JS transport/DOM are stand-ins.
2. Supply fresh unchanged-policy guard admission for a never-shown desktop,
   with fixture HWND allowlists and evidence of foreground/focus/cursor/input
   desktop continuity. Historical reader rejection was
   `house observation stale/unknown/unsafe`. The observation issuer/kernel
   House with JEFF resolves that admission, without credential/ACL/policy
   changes or copied/manufactured observations. Stop on refusal.
3. Independently exercise the shipped dock component through its widget
   principal and production WM dispatch against fixture-owned native windows.
   Do not switch the input desktop, send live input, launch games, touch real
   app windows or terminate Alex's programs. Never show a fixture on his
   desktop. Existing broad native proof scripts include lifecycle/watchdog
   scenarios outside this task; do not replay them wholesale.
4. Measure both maximized and borderless/composited fixtures, saved normal
   bounds, existing minimized and newly opened targets. Verify window-state
   restoration occurs before placement; real resulting visibility,
   nonoverlap, useful bounds, remembered preferences and settling without
   oscillation. A real app may decline SC_RESTORE: verify one bounded failed
   geometry probe leaves it visible and brings the request in front at its
   remembered bounds, with an explanatory WM record. Never minimize that
   fullscreen participant as fallback.
5. Cover all six opening orders of browser-class Claude, small Spotify and
   Agora/JEFF chat; all three must be visible/usable when the work area can
   hold their minima. Check Chrome at least half work-area width, including
   odd widths, pressure and close; closing each participant must grow
   remaining tiles. Force capacity exhaustion and verify true LRU alone
   steps aside when one slot suffices, never the incoming app. Check fresh
   Agora opening arms before `window.open`, and a new explicit bar request
   re-probes an already flagged window.
6. Confirm no learned-failure "can't join shared layout" rejection; pins,
   explicit exclusions, dialogs and sleeping apps retain their policies.
   Exclusive/unknown/inspection gates remain closed. Expiry and denied
   native operations stop without retry, lease release/reacquisition or
   lifecycle fallback. Record exact test output and guard receipts.

The draft does not include a new executable native hidden-desktop harness.
House must supply its independent guarded native execution; the authored
controller and method-seam checks do not replace it.

## Smallest supported activation: JEFF only, after review

1. House reviews, commits and lands the approved source; worker does none of
   these. JEFF verifies the actual WM run target will import the reviewed
   `manager.py`, `engine.py`, `win32_host.py` and `wm_module.py`. Repository
   landing alone does not change imports in the living process.
2. There is no supported hot replacement. `wm.reload` is not an activation
   route; do not try it, retry a refusal, change the run path on a living
   process, or add keepalive/claim workarounds. JEFF owns any separately
   permitted WM-only activation opportunity. Latest card assigns WM off/on
   to JEFF after review; this worker's no-restart constraint remains binding.
   If JEFF's current authorization does not include lease/geometry effects,
   stop and name that exact missing lifecycle authority to Pike.
3. For an explicitly authorized WM-only off/on: one `off wm`, then confirm
   old WM exit and identity/cookie-checked lease release completed before
   one `on wm`. Existing module shutdown can terminate the WM process and
   restore saved geometry/styles/claims; a new startup may rearrange windows.
   It cannot promise exact geometry preservation. Stop on refusal, timeout,
   incomplete release or run-target mismatch. No second attempt, manual
   claim repair, shell/kernel/window-host restart, app closure or draft reload.
4. After authorized activation, JEFF checks fresh `help wm.arrange`,
   `wm.windows` and `wm.policy` against reviewed expectations. The existing
   startup manifest covers direct Manager/Native methods and their local
   top-level functions; it does **not** attest the engine or the whole
   process. House/JEFF must establish reviewed engine provenance separately
   through the verified checkout/run target and fresh process, without
   claiming that the limited manifest proves it.
5. Compare fresh stored shell code with the reviewed source. For this draft
   the only shell-source delta is `Data.launch`'s `window.open` expectation.
   Patch only that exact uniquely matched helper span in the existing
   widget code that hosts the dock (historically dk788). If the top widget
   (historically dk785) also uses that helper for opening, update the same
   span there only. Preserve every other byte and stop on concurrent edits
   or an ambiguous/missing match. Do not regenerate `shell_code()`, replay
   an installer, replace lenses or change unrelated shell components.
   Earlier landed `Data.focus` and dock-item routing should be verified,
   not blindly replayed as new changes.
6. Verify the existing dock widget principal has `wm.arrange` and the
   existing focus/restore/open words. No security/grant change is authorized
   here. If absent, report exactly: operation `wm.arrange`, calling dock
   widget principal, missing capability, resolver JEFF/kernel steward.
   Stop rather than changing grants or substituting another principal.
7. Reload only shell pages whose helper code changed, by their fresh page
   identities (historically dock dk792 and top dk791). Never reload all pages
   or draft-bearing apps. Verify unchanged lens facts and unrelated shell
   arrangements, app/page identities and drafts; capture any WM-only geometry
   effects explicitly. This source worker performs no world activation.
8. Record permitted owner observation on both cards: Claude/Spotify/JEFF chat
   opened from the bar in any order, Chrome useful half width, close growth,
   no join failure and no fullscreen fallback minimization. Alex's outcome,
   not merely a successful build or shell reload, closes acceptance.

## Exact blocked boundaries and limitations

- Worker live `wm.windows` was denied: desktop owner Alex dk2, or authorized
  steward/agent, owns that operation. JEFF dk827 supplies facts and verifies;
  worker does not retry under another identity.
- Historical fixture cleanup enumerations were denied under this worktree's
  `.tmp/dk1706-fullscreen-*`; House owns future fixture admission. The worker
  did not repair permissions, delete those directories or retry traversal.
- Hidden native admission requires a current House-owned observation, not a
  worker-edited guard snapshot. The exact historical reason appears above.
- WM module dk532 is the lifecycle target; JEFF/kernel steward is resolver.
  No arrangement-preserving live replacement exists. Never imply an off/on
  preserves in-memory intent, claims or exact window placement.
- Exclusive fullscreen is unsupported. SC_RESTORE asks an application's
  window-state handler; it cannot force internal Electron/browser fullscreen
  cooperation. Declining apps use the recorded foreground fallback. No
  keystroke, game/display-mode or settings workaround is supplied.

Both cards remain open for House behavioral review, guarded native evidence,
JEFF activation verification and the owner outcome.
