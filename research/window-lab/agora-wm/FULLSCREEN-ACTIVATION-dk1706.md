# Fullscreen sharing closeout — held for JEFF

Follow-up: JEFF authorized source-only delivery repair, with no off/on, guard
retry or activation. See [WM policy handoff](POLICY-RELOAD-dk1706.md) for the
current refusal-only resolution, tests and exact lifecycle exception needed.
The earlier reload design was withdrawn after provenance/stall review; there
is no supported live replacement path. The observations and rejected
admission below remain historical evidence; they have not been sampled again.

Builder handoff, 2 November 2026 Pacific / 3 November UTC.
Source inspected: `43ef35f04f4ed52583861e859736e8589de7d12a`.
No activation, source correction, test window, application launch, input,
termination, credential or settings change was performed.

## Evidence and present state

**Read:** the exact six-file landed diff and the corresponding worktree source.
The worktree has no further differences in those six files. The patch adds a
five-second bar-requested share transaction to the existing solver; normal
placement dimensions for maximized windows; screen-sized frameless candidate
classification; `share=yes` focus/restore and `wm.arrange expect=<exe>`; and two
dock executable-launch routes. It does not add another tiling engine.

**Read, live through Agora:**

| Surface | Observation |
| --- | --- |
| `status wm` | `wm: live; 23 windows` |
| `help wm.arrange` | Old help, takes nothing; no expected-executable argument |
| `wm.windows` | Old public rows, without the new `display_mode` field |
| shell-top widget `dk785`, revision 2077 | Stored code lacks `share=yes` and `async launch(line, exe)` |
| shell-dock widget `dk788`, revision 2076 | Same missing helper changes |
| shell-dock-item component `dk782`, revision 1240 | Code lacks `Data.launch`; old reviewed hash `31a880096bc28f9f7c5057d2c4f3489cf046b29eb3f3aa20e7bf718e6e54e6df` |
| Grants `dk786`, `dk789` | Existing shell grants lack `wm.arrange`; existing write scope is `kind:shell-settings,button,ask-request` |
| `window.list` | 12 Agora windows, including dock `dk792` and top `dk791`; Writing and other apps remain open/tucked |

These independent live observations establish that landing did not activate
the feature. Do not infer loaded Python bytes from the module's `run` path:
the already-running process keeps its imports.

**Read, independent historical review:** task history records review of this
exact commit at `r3500`, success at `r3502`, and landing at `r3556`.
`research/kernel-lab/modules/house/builders.py`, `CHECKS`, identifies the gate as:

1. `research/kernel-lab/tests/test_chat.py` and `test_paint_health.py`;
2. `research/window-lab/kernel-desktop/test_kdesk.py`.

That gate does not run the WM manager tests or a maximized/borderless dock-click
proof. No fullscreen-specific success count has been independently established.
The old worker's BUILD-RESULT reports `27 failed, 6 passed, 2 warnings, 2 errors,
4 subtests passed in 2.65s`, with filesystem denials, and explicitly says its
draft was unvalidated. Those results are historical, not rerun here.

## Exact blocked boundaries

**Ran, read-only preflight once:** pinned
`C:\Projects\Agora4\.venv\Scripts\python.exe -B` imported
`research/text-desk-lab/notation/guard_context.py` and called `read()`.
It returned `admitted=false`, reason `house observation stale/unknown/unsafe`.
The fixed observation had `observed_at=1793129324.3414583`,
`issuer_pid=11724`, `foreground_exe=claude.exe`, notification state 2,
`full_screen=true`, `game=null`, and `admitted=false`.
No desktop or fixture was created. No retry followed.

Operation blocked: admission to guarded hidden native validation.
Principal: this managed coding worker is a reader, not the House observation
issuer. Resolver: JEFF / the kernel House steward must provide an approved,
current House-owned admission path for the kernel world. The reader's fixed
path is
`C:\Projects\Agora4\research\text-desk-lab\notation\house-state\frontier\guard-context.json`.
Source search found its `Publisher` integration only in the old notation
House, not `research/kernel-lab/modules/house`. This is an integration gap to
resolve, not permission to copy a snapshot, impersonate the issuer, change
the non-game list, manufacture admission, or bypass the guard. The observation
is stale; its foreground facts do not describe Alex's present desktop.

**Ran, evidence discovery:** `rg --files` against the main desktop `state`
directory encountered `Access is denied` for existing `edge-kdesk-*` and
`icons-*` directories, including `edge-kdesk-cwn11crn`. Discovery stopped; no
traversal retry, alternative traversal, ACL change or cleanup followed. Exact
independent check output/counts therefore remain unread. House can supply its
own already-owned check receipts through the world; the worker must not
repair those directory permissions.

Operation blocked: loading changed Python into the existing WM process
without a prohibited lifecycle change.
Principal: WM module `dk532` runs for desktop owner Alex (`dk2`); JEFF
(`dk827`) is the coordinating steward. Resolver: JEFF / kernel House.
`kernel/modules.py:Host.reconcile` starts only absent/dead modules and stops
those removed from the wanted set. It does not replace a living module when
its `run` changes. `window.reload` reloads pages only.
The available `off wm` / `on wm` route stops the module, revokes/restores its
grants and releases WM holds; WM lease release can restore saved geometry.
This violates the current no-termination/settings constraint and cannot be
offered as an arrangement-preserving activation. No such operation was tried.
JEFF needs a separately authorized bounded lifecycle decision, or a permitted
later lifecycle opportunity. Do not kill a process, change `run`, toggle
`wm.mode`, restart kdesk/window host, or retry a denied operation.

## Smallest conditional shell activation

This is a handoff for JEFF, **not authorization to activate now**. Keep it
held until the admission, feature proof and WM lifecycle requirements above
are resolved. Do not partially update the dock against the old WM: the old
module can silently ignore the new arguments.

1. Read fresh `look`/`rows` for WM, both widgets, both grants, the dock-item
   component, both shell lenses, `window.list`, `wm.windows`, and WM settings.
   Preserve their original code/facts and screen observations in House-owned
   evidence. Check that no concurrent shell edits invalidate this handoff.
2. Once a permitted WM-only activation has occurred, confirm
   `help wm.arrange` advertises `expect=<exe>` and exclusive-fullscreen limits,
   and fresh `wm.windows` includes `display_mode`. Keep the desktop/window host
   and every app running.
3. Patch only the changed `Data.focus` helper and inserted `Data.launch`
   helper from the landed `shell_parts/shell-kit.js` into each existing widget's
   stored `code`. Use exact, unique old-span matches from the parent of
   `43ef35f04f4e`; stop if missing, duplicated, or concurrently edited. Preserve
   all other stored bytes. Do not replace either widget with a freshly
   generated `shell_code()`: that would also replay unrelated painter changes.
4. Patch only the two executable-launch spans from the landed
   `shell_parts/components/shell-dock-item.js` into component `dk782`'s existing
   `code`, again requiring unique exact old spans and preserving other bytes.
   Through ordinary world words: `look dk782`, `set dk782 code=<JSON string>`,
   `look dk782`, `component dk782`. Inspect and review the exact resulting code.
   Set the two widget code fields through the ordinary `look`/`set` path too.
5. If still absent, JEFF supplies the single missing word to the **dock**
   widget principal through `grant dk788 words="wm.arrange"
   only=kind:shell-settings,button,ask-request`, subject to his authority for
   that capability change. Do not replay the full grant list or revoke existing
   grants. The top bar has no executable-launch route requiring this addition.
6. Reload only the two shell pages in place:
   `window.reload dk792`, then `window.reload dk791`. This is the smallest
   existing page refresh; it avoids reloading draft-bearing app pages.
   Do not use `all`, `window.shell off/on`, `off`, a full shell installer, or
   `--reset-lenses`. The installer visits every component, both lens facts and
   widget configuration, beyond this task.
7. Reread code and reviewed hashes, capability, WM help/rows, both unchanged
   lens arrangements, window identities/positions, shown/tucked states, and
   absence of reload errors. Confirm app pages and their drafts were not
   reloaded. A page reload is not itself dock-behavior acceptance.

## Required validation and acceptance

**Unrun, required:** after JEFF resolves admission, perform one guarded hidden
validation using fixture-owned HWNDs, never Alex's real Claude/Spotify/game.
Use a fresh private world and actual dock component click, routed through its
widget principal and production WM request dispatch. A mocked `Data.act` or a
direct manager call alone does not prove that path.

Cover both an existing/restored app and a new executable fixture, alongside
(a) a maximized fixture with saved normal bounds and (b) a screen-sized
borderless fixture. Assert actual resulting native visibility, nonoverlap,
in-work-area geometry, remembered dimensions where feasible, settled bounds
without oscillation, and unchanged pins/exclusions/dialogs. Include a
foreground/gate change, transaction expiration and unrelated-window arrival.
Verify D3D/exclusive and unknown/inspection-error gates fail closed.
Record the guard's foreground/focus/cursor/input-desktop continuity evidence;
never synthesize live input or claim a zero foreground reading proves safety.
No browser launch or process cleanup should be attempted without the approved
fixture ownership/lifecycle boundary. Stop on the first refusal; no retries.

**Read, limitation:** exclusive fullscreen is unsupported. Win32 coverage of a
monitor cannot prove composited presentation; source retains notification
states 1/3/4/7 and inspection failures as gates. Some composited games can also
remain gated. No display-mode forcing or game settings change is supported.

**Acceptance remains unverified.** Hidden proof establishes only its measured
cases. JEFF must record a permitted owner outcome showing the requested bar
opening makes both apps visible with sensible bounds; this worker must not
manufacture that outcome using live input. Keep the parent and closeout tasks
open until activation and outcome evidence exist.
