# Source audit: desktop host and window manager (26 Oct – 3 Nov 2026)

*Evidence for [[SOURCE-EDITS-AUDIT]]. Written by a read-only helper Claude started on 4 Nov; kept as it reported, lightly
trimmed. Labels: **read**, **ran**, **imagined**.*

Scope (ran): 59 non-merge commits touch `research/window-lab/kernel-desktop` or `agora-wm`. Per day: 26 Oct 16, 27 Oct 23,
28 Oct 14, 29 Oct–1 Nov 0, 2 Nov 1, 3 Nov 5. Per file: kd_window.py 21, kdesk.py 17, shell.js 11, widget-host.js 9,
shell-kit.js 7, wm_module.py 7, win32_host.py 7. Read: diffs (tests/evidence/md excluded), SHELL.md rough spots 1–20,
ROUGH-SPOTS-WM.md; cards dk1613, dk1656. The uncommitted tree was not audited.

| commit | what | class | avoidable | how / rough spot |
|---|---|---|---|---|
| 0a13edce4 | painter fault isolation, upload cap, stall watchdog in the bridge | U/S | no | |
| cf135a623 | Blob transport, download chooser, `project` op | U/S | no | |
| 8df3c934f | drop "Widget · " title prefix (3 files) | P | yes | Title is the widget's own fact |
| 626c1238d | the WM: engine, Win32 host, module, watchdog | S+U | Win32 part no | ROUGH-SPOTS-WM |
| 78116cccc | busy gate exempts 7 shell-overlay exes | G+P | partly | Exe list as a gate setting |
| 395b9e07f | shell bars, layer, SHELL_VIEWS, AppBar, `window.shell`, `/desk/icon`, theme routes, 918-line shell.js | S+U+C+P | partly | Rough spots 1–7 |
| f40ff0e13 | dock icon families via regex | P/C | yes | An `icon=`/`app=` fact |
| a3d4a15fa | geometry and pins out of the world; glass bars | U+G | no | Rough spot 10 |
| 0b6cebead | WM feel; tunables into wm-settings | U | partly | ROUGH-SPOTS-WM |
| 98a2d7407 | 17 bar components shipped as files then installed; `window.native` hold | C+U | partly | Rough spots 8–13 |
| ab4483153 | wm words `undo=no` | G | partly | |
| 63ef9402e | engine fills free space first | G | no | |
| 96e2a6236 | restore keeps min state; dock poll 1 s→2.5 s in two copies | G+P | partly | |
| 30efd6bc9 | tucked windows kept locally | G | no | |
| 1ddb6425b | `window.launch` takes Start-menu shortcuts | S | no | |
| db8a27e00 | minimised painter windows not judged hung | G | no | Rough spots 15–17 |
| 6d5f93d29 | `media.pause`/`resume` | U | no | |
| 4b40b7b18 | `Agora.Desktop` mark + `is_desktop` in 4 files; `window.open url=` | G+U | partly | Superseded the same day by 5d8d1bda0. Rough spots 18–19 |
| 397a55b5c | `moving_in()` seeds JEFF, chats, house-agent with model names; JEFF session; lens + 681-line style as files | B+C+P | mostly | A reviewed seed/kit act; only session minting needs the host. Not logged |
| 102c30f8e | team group in the seed | B+C | yes | Not logged |
| 6eae88530 | bar click region until the page sends its shape | G/S | no | |
| 6d64c084e | Work icon + `AGORA_APPS` entry | C/P | yes | App as a world thing |
| f62c84eb6 | wm admits stewards, polling `who` each 1 s | G (dup) | partly | Kernel-enforced role |
| 5d8d1bda0 | wallpaper.py; the layer row becomes a wallpaper flag | S+B | partly | Rough spot 20 |
| de0acdb3b / 13772595b | Writing icon; Work and Writing into the shell-kit copy | C/P | yes | "app list lives twice; icon= fact should be enough" |
| 0a309676b | window module admits stewards (second copy) | G (dup) | partly | |
| 807ef5ecf | bars are tool windows before showing | G/S | partly | |
| 26e247f52 | dock acts on Agora windows by id (3 copies) | G in C | partly | |
| a0aabf673 | WM adaptive repack | G | no | |
| 20e82141d | window on a thing passes `$view.target` | U | no | |
| f953920cf | per-window WebView2 profile | G/S | no | |
| 38ef957df / a6e5756e4 | NVIDIA readout room (3 host + 2 page files), then reverted | B | yes | Bar insets as a setting |
| c58ca70c3 | refusals log | U | no | |
| 184810424 | WM standing mode vs one-time request | G | partly | |
| 6a71e5443 | grants at start; dead pages; stop asking `wm.title` (2 copies) | G+P | partly | |
| fc9f21bfe / 8034eafbe | `--resident-manifest`, `add_person_session` | B | partly | |
| 4c259b5d4 | "rowan"/"rowan-builder" in LocalEntry | B/P | yes | |
| 458a7c36b | help text "Sable or Pike" | B | yes | |
| 39f996a3b | non-owner stewards see the program, never the title | G | partly | |
| 8a8aa6a02 | worker sessions for every house-agent's person | U/S | partly | Driven by world things; fine |
| 9fbbfbaa5 | keeper, `kd_reload`, `window.reload`, job object | S+U | no | |
| 544689d99 | restore intent supersedes pending work (Spotify) | G | no | |
| e807ce9c6 | white blocks: pywebview navigation patch | G/S | no | Not logged |
| ba6d0a044 | shared right-click `menu.js`; menu policy hard-coded (chat "Conversation", Needs-you rule) | U+P | partly | |
| 43ef35f04 | fullscreen share window; another `covers_monitor` | G/U+P | partly | Not logged |
| 4ec84d22b | Twitch module + installer at every start, channel hard-coded | B+C+S | mostly | Adapter word (22 Oct design). Not logged |
| ff951ea68 | Viewer: native pane; 4 `view=="viewer"` branches; startup pin; app list ×2 | S+B+P | partly | Not logged |
| a3e433940 | Twitch survives a kernel restart | G | no | |
| 2c9db8213 | media shuffle/repeat; Music added to shell-kit.js only | U+C/P | partly | Dock entry avoidable |

**Tally (judgement):** U/S ~11, G ~21, B ~10, P/C ~10, T/docs ~7. About 25 commits mostly or partly avoidable. About 30
name a missing word somewhere, across 12 places; the worst offenders (JEFF/team seeding, Rowan, Twitch, Viewer, Music, dock
icons, 43ef35f04) log nothing.

## Hotspots (read)
- kd_window.py 21: `GuiScreen.open`/`loaded` changed 7 times, each new window kind (bar, layer, tucked, glassy, viewer) a new
  branch fighting pywebview at a different moment; `window.open` 4 times; `reconcile` and bars 5.
- kdesk.py 17: 11 of them seed or provision the world at start (people, chats, sessions, grants, pins, Twitch).
- shell.js + shell-kit.js + shell-dock.js: the same lists live in the hand-written fallback and the components; fixes land
  2–3 times and the copies drift (shell.js:145-152 lacks `music`).
- WM placement policy rewritten 4 times in a week. Side effect (read): the world setting `when_full` is still validated at
  manager.py:53 but the engine no longer reads it. A world preference went dead silently.
- The desktop layer: made 26 Oct, fixed across 4 files 27 Oct, removed 27 Oct.

## Hard-coded preferences (read)
- kd_window.py:54 LENS_SIZE; :55-58 VIEWS; :83-84 bar heights; :86-87 SHELL_VIEWS; `view=="viewer"` at :354,357,379,433;
  :358 background colour; :788 spots; :931-935 title masking; :1157-1161 auto legacy taskbar; :1165-1167 layer row as wallpaper flag
- shell_native.py:61-62 sizes
- kdesk.py:52-60 grants and JEFF_ACCOUNT; :122-164 Viewer pin; :193-241 moving_in (JEFF, Conversation, Shop talk, team, models);
  :251-253, :292-308 sessions; :537-538 Twitch install on every start
- twitch_chat.py:14 `channel="dr_bizzlebop"`; raises on any refusal; re-makes a deleted pin
- shell-kit.js:75-91 AGORA_APPS, DOCK_APPS, appOf regexes, :121 exe names; shell.js:58, :145-160, :186, :536, :722-723;
  shell-dock.js:27 built-ins; polls at 2500 ms; `"window.open lines"` fallbacks ×4
- menu.js:120-121 the chat "Conversation" by name; live.py:78-86; gaming_gate.py:7-10 game exe lists; wallpaper.py:48 Edge path
  and 5 s poll; viewer.py:21-25 colours; jeff_chat.py:37 and twitch_chat.py:38 hack the painter id
- WM: win32_host.py:202-203 SHELL_OVERLAYS; engine.py:29-30; manager.py:12 DEFAULTS, :53 `when_full` (dead)

## Duplicated ideas / missing shared seams (read)
1. "Covers the monitor": 6 copies (gaming_gate.py:63, kd_guy.py:339, kd_window.py:490, win32_host.py:183 and :190,
   widget_overlay.py:67). Only `is_desktop` was unified.
2. Steward check polled twice (`who` every ≤2 s and every 1 s).
3. Dock app list ×2–3, plus 12 app SVGs in source.
4. Bar behaviour twice (hand-written fallback and components).
5. CDP clients ×3 in this area (14 across the repo); wallpaper.render skips the kill-on-close job added after 42 leaked browsers.
6. DPI read two ways. 7. Three lens-file installers with id substitution. 8. `SetPropW("Agora.Window.")` in three branches.
9. Polling in place of hearing: who, theme hash, wm.windows, wm.title.

## wallpaper.py (judgement on read code)
Keep the behaviour, not the shape. Of 365 lines: ~87 are the OS seam (save, set, restore, Spotlight caveat) and should stay;
~127 are a private renderer duplicating `widget_browser.Browser`; ~64 are glue (polls theme.json every 5 s because the window
module cannot hear theme things; driven by a window thing that no longer makes a window). Smallest world-level set: a shared
`render <lens> size=` word returning a file thing; `system.wallpaper` see/set with the before-state kept so undo restores;
one world rule on theme change. Windows `.theme` files apply through the Settings UI, so not for applying. What would change
the helper's mind: wanting a live or animated wallpaper, which needs a window again.

## Missing mechanisms (counts are the helper's attribution)
1. **A world seed/install act** (a reviewed kit run by a word; the host only mints sessions). 11 (kdesk.py). Named 24 Oct ("No install word").
2. **One owned host window lifecycle with declared roles.** 9. A host abstraction: localises edits rather than removing them.
3. **Apps as world things** (label, icon, opens-line). 8.
4. **One screen-facts seam, with gate exemptions as settings.** 6.
5. **An unrecorded live channel** (ephemeral happenings or live aspects). 4.
6. **The kernel enforcing the caller's role before a module sees the call.** 3.
Also: an adapter word (Twitch), retiring or merging the hand-written bar fallback (~5 double edits).

## The helper's thinking (imagined)
Host source does three jobs: the OS seam (legitimate), seeding the world at every start (JEFF, Rowan, Twitch, pins, grants),
and carrying the shell's content (app lists, icons, menu policy, lens files). Only the first belongs in source. The quiet
days (29 Oct–1 Nov) are not a downtrend: 3 Nov's 5 commits include three new bespoke features (Twitch, Viewer, Music), and
Viewer and Music both edited the dock list again. What would change its mind: a week of new apps landing with zero host diffs.
