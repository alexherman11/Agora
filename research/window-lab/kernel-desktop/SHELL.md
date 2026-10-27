# Agora desktop shell: top bar, dock, desktop layer

Written 26 Oct 2026 by the shell builder. A draft for Claude and Alex to adopt; nothing here is live. Labels: **ran**
(executed, output quoted as printed), **read** (primary source read), **imagined** (design, not exercised).

Nothing was installed into, restarted in, or sent to the live desktop (127.0.0.1:8810), its keep/sessions.json, window
origins, Explorer's taskbar or any AppBar. All proof is headless Edge, scratch kernels and a hidden Windows desktop
(`research/window-lab/sandbox_window.py`). The only contact with real windows is a read-only `EnumWindows` of
Progman/WorkerW and `WM_GETICON` on existing windows in `test_shell_icons.py` and the survey in `shell_proof.py spikes`.

## What was built

| Piece | Where | What it is |
|---|---|---|
| Top bar | `pages/shell/top.html` + `shell.js` (`Top`) | Slim translucent rail. Every element is a button with a popover: launcher, focused app's window menu, clock (calendar), notifications, media, one quick-settings cluster (network, volume, battery), JEFF, off (two presses). Optional readings (CPU, memory) are off until `shell-settings` says so. |
| Dock | `pages/shell/dock.html` + `shell.js` (`Dock`) | Centred floating pill. Real colour icons, grouped by exe, running / in-front / minimised marks, a stable remembered order, pinned Agora apps and world pin buttons. Click, middle-click (new window), right-click menu, hover preview. All through `wm.*`, with `native_shell` words when the WM is off. |
| Desktop layer | `pages/shell/desktop.html` | Agora's own layer under every app; draws the theme's wallpaper, live with the theme. Never touches the system wallpaper. |
| Icon pipeline | `shell_icons.py`, route `/desk/icon` in `kdesk.py` | See below. |
| Native seams | `shell_native.py` | Window shape (`SetWindowRgn`), reserved strips, DWM thumbnails, bottom-most layer, opt-in WorkerW attach. |
| Host wiring | `kd_window.py`, `native_shell.py`, `kdesk.py` | Shell views, `window.shell on\|off`, `/desk/icon`, icon refs on window rows. |
| Proof | `shell_proof.py`, `shell_spike_window.py`, `shell_spike_desktop.py`, `test_shell_icons.py` | Hidden and headless. |
| Stand-in looks | `pages/shell/looks/*.css` | Seabright Day, Dusk, Night Metal, Ink Landscape, written to the same `--ag-*` names the theme compiler emits. |
| Agora app icons | `pages/shell/apps/*.svg` | Lines, Board, Appearance, Task board, Help, Feed, Overview, Thing, Desktop, Agora: a squircle plate, a soft light, a white glyph. |

### Shared-file edits (re-read before each edit; backward compatible with the running process)

- `kd_window.py`: `SHELL_VIEWS`; `_make_bar` handles `edge=layer` and shell views; `AppBar.resize`; `PageApi.layout/thumbs/title`
  and `GuiScreen.shell_layout/shell_thumbs`; word `window.shell on|off` (one act, so one undo); `window.activate` passes
  `do=` (`do=close`); legacy taskbar auto-creation is skipped while a shell row exists; `layer` rows skip placement and drag watching.
- `kdesk.py`: the owner-only `/desk/icon?ref=&size=` route (`Cache-Control: private, max-age=3600`).
- `native_shell.py`: window rows gain `ref=` (the old `icon=` stays for the legacy taskbar); `activate(handle, exclude, do)` posts `WM_CLOSE` for `do=close`.
- New files only otherwise. Painter and `kernel-lab/components` were not touched.

## Why not components

The bars are host pages under `pages/shell/`, not sandboxed painter components. A bar has to talk to its own native window
(shape, reserved strip, DWM thumbnails, `AppBar.resize`), and the component frame has no native bridge. They are still small named
parts with handles, and they read only `--ag-*`, so a theme restyles them like any component. What would change this:
a component frame with a `native` capability (layout, thumbs), after which the parts can move without losing anything.

## Components and their handles

World things the shell reads, none required (every one has a default):

- `kind=shell-settings`: `show_cpu`, `show_memory` (`yes` shows an optional reading), `dock_apps` (comma list of Agora apps pinned
  to the dock, default `lines,help,board,taskboard,appearance,feed`), `jeff_open` (the line the JEFF popover runs).
- `kind=button bar=taskbar path=<exe>`: existing taskbar pins; the dock shows them as pinned apps.
- `kind=window shows=shell-top|shell-dock|shell-desktop`: the three shell windows `window.shell on` makes.
- Data read: `wm.windows`, `system.now`, `media.now`, `rows notification`, `rows presence`, `rows shell-settings`, `rows any bar=taskbar`, `rows lens`, `wm.title <key>` (live titles, tolerated if refused).
- Acts sent: `wm.focus|minimise|restore|close|pin|unpin <key>`, `window.launch path=`, `window.open <lens>`, `window.start`, `media.play|next|prev`, `wm.mode off`, `off window`, `make kind=shell-settings ...`.
- Every page also exposes `window.__shape` (rects and radii the host turns into a region), `window.__ready`, and `window.Shell` for the proof.

## Theme contract

Read: `--ag-bg --ag-surface --ag-raised --ag-ink --ag-ink-muted --ag-text --ag-accent --ag-accent-soft --ag-accent-ink --ag-border
--ag-border-w --ag-hover --ag-focus --ag-danger --ag-warn --ag-ok --ag-radius-s/m/l/pill --ag-gap-inner/outer --ag-bar-height
--ag-bar-bg --ag-bar-opacity --ag-dock-size --ag-backdrop --ag-wallpaper --ag-wallpaper-size/pos/repeat --ag-wallpaper-dim
--ag-shadow --ag-font-ui --ag-font-display --ag-icon-plate --ag-icon-tint --ag-motion-reduce --ag-dur-* --ag-ease`.
Fallbacks in `shell.css` are lengths and numbers only, never colours, so a theme that omits a colour is visibly incomplete, not silently wrong.

Gaps to settle with the theme builder (observed in the compiler's output; not changed by me):

1. `--ag-icon-style`, `--ag-island-opacity`, `--ag-island-outline` are consumed by the shell (icon style native/plate/mono, translucent
   islands, an island outline) but are not emitted by the compiler. The stand-in looks set them; a real theme gets the defaults.
2. `--ag-wallpaper-dim` is emitted as a colour; the shell treats it as a colour layer over the wallpaper.
3. `--ag-border` is a colour in the contract and a width in some themes (`--ag-border-w` is the width). The shell uses `--ag-border-w` only.

## Window shape: how it works and what is lost

> **Superseded in part, Claude, 26 Oct 2026 (live, on Alex's screen).** The region does NOT clip a WebView2's
> drawing on the real composed desktop: Alex saw the whole bar and dock windows as white boxes (**ran**: pixel
> (255, 255, 255) at 1900,400 under the 840 px top-bar window; shrinking that window removed it; re-applying the
> region, redrawing, and setting the region on every WebView2 child changed nothing). Spike 1 D printed the same
> white as its "corner pixel" and was read as a pass because hit-testing passed. Spike 1 A (transparent=True)
> painted its corner black, and black is what DWM glass treats as see-through. Now: the two bar windows are
> `transparent=True` and `shell_native.glass()` extends DWM glass over the whole client area; the region stays,
> for clicks only. **ran** after: the same points read wallpaper (93,69,160) and dock-area purples, no white.
> This also opens what the paragraph below says was lost (translucency over other programs, shadows, smooth edges);
> not yet used or measured.

Windowed WebView2 cannot be per-pixel transparent (spike 1). The shell therefore:

- clips each window with `SetWindowRgn` from rounded rects the page reports (`__shape`);
- draws a **wallpaper slice** in each page at its own screen offset, so translucency, blur and rounded corners read correctly over the desktop layer;
- makes a bar or dock window larger than what shows (room for popovers) and clips the rest;
- reserves the screen strip with a separate invisible AppBar (`AppBar.resize`, from the page's `reserve` css px);
- keeps the dock ring (pill plus `min(--ag-gap-outer, 8px)` each side and `--ag-gap-outer` above and below) inside the reserved strip, so it never covers an app.

Lost: real translucency over *other programs* (the bar is translucent only over the desktop layer), drop shadows on the bars,
popovers and dock (a region cannot carry one; popovers are solid), and anti-aliasing at region edges (spike 1 D: 781 blended edge
pixels per corner, a hard-edged region; A to C show colour-key tricks fail differently).

## Spike results (ran, as printed)

Spike 1, window shape (hidden desktop, WebView2 in pywebview):

```
A-pywebview-transparent: corner pixel in the window's own paint (0, 0, 0); hit test at the corner passes to the window behind: False, at the centre reaches this window: True; layered=False key=0x0; blended edge pixels per corner 73
B-colorkey-black: corner pixel (1, 2, 3); corner passes to the window behind: True, centre reaches this window: False; layered=True key=0x30201; blended edge pixels per corner 73
C-colorkey-edge-tone: corner pixel (205, 180, 254); corner passes through: True, centre reaches this window: False; layered=True key=0xfeb4cd; blended edge pixels per corner 62
D-region: corner pixel (255, 255, 255); corner passes through: True, centre reaches this window: True; layered=False key=0x0; blended edge pixels per corner 781
```

Read: only the region (D) is both see-through at the corners and clickable in the middle. The colour-key variants lose the centre's hits.
Screenshots: `evidence/shell/spike-window-*.png`, `spike-window.json`.

Spike 2, the desktop layer (hidden desktop, `spike-desktop.json`):

```
shell_window: 0   progman: 0   workerw: 0   defview_anywhere: False
attach_workerw_result: not tried: there is no Progman on this desktop to send 0x052C to
layer_mode: bottom   layer_exstyle_toolwindow: True   layer_exstyle_noactivate: True   layer_exstyle_appwindow: False
z_front_first_initial: ['app-B', 'layer-A']   z_after_a_raise: ['layer-A', 'app-B']   z_after_keep_loop: ['app-B', 'layer-A']
layer_below_app_after_loop: True   layer_became_foreground: False
live desktop structure, read-only (no message sent): Progman present: True; its direct children: ['SHELLDLL_DefView']; WorkerW top-level windows: 16 of which visible: 0.
So SHELLDLL_DefView is Progman's own child (the 24H2 structure), not inside a WorkerW
```

Read: a desktop made by `CreateDesktop` has no Explorer, so **the WorkerW method could not be run** there. On the live machine (build 26200)
the 24H2 structure is present, where the classic "spawn a WorkerW and parent behind the icons" trick is unverified. The default layer is therefore
a bottom-most tool window (`WS_EX_TOOLWINDOW|NOACTIVATE`, kept at `HWND_BOTTOM` by a loop, never foreground; the loop restored the order within 1.6 s).
**What is lost with the fallback:** it covers the desktop icons (Explorer's icons are under it), and a program that raises a window to the very bottom briefly shows through
until the loop corrects it. The opt-in `AGORA_DESKTOP_LAYER=workerw` attaches under the icons; it is **not verified** on 24H2.

## Seam proof (ran): does the slice match the layer?

Desktop layer alone vs the bar and dock windows over it with their parts hidden, 3840x2160:

```
seam real:seabright-day: 31025 of 8294400 pixels differ, 8251 by more than 2 levels, largest difference 9, inside (6, 43, 2817, 2160)
seam real:dusk: 94338 of 8294400 pixels differ, 49073 by more than 2 levels, largest difference 12, inside (0, 26, 2855, 2160)
seam real:ink-landscape: 2109 of 8294400 pixels differ, 327 by more than 2 levels, largest difference 71, inside (1327, 2055, 2513, 2160)
seam standin:dusk: 126287 of 8294400 pixels differ, 49034 by more than 2 levels, largest difference 35, inside (0, 19, 2863, 2160)
```

Read: the gradients agree to within a few levels except at rounded region edges (the ink maximum is 71 on 327 pixels of a crosshatch edge).
The first version of the dock ring (48 px each side) showed a faint notch over a neighbouring window's shadow (max 17); narrowing it to `min(gap, 8px)` brought the seabright-day maximum to 9.
Not measured: the seam over a real DWM-composited desktop; only the page-level composite is proven.

## Icon pipeline

`shell_icons.py`; the page asks `/desk/icon?ref=<ref>&size=<64..256>`; `SIZES = (64, 96, 128, 192, 256)`, the dock asks for 128.

- Refs are strings: `exe:<path>`, `hwnd:<n>`, `pkg:<PackageFullName>`, `aumid:<id>`, `agora:<app>` (the SVG set).
- Source order: package manifest logo, then `IShellItemImageFactory` (ICONONLY|BIGGERSIZEOK, ctypes vtable), then `ExtractIconEx`, then the window's own icon
  (`WM_GETICON` big, then the class icon; a two-pass black/white background trick recovers alpha).
- Disk cache `state/icon-cache/<sha1>-<size>.png`, keyed by exe path + mtime + size (`AGORA_ICON_CACHE` overrides the directory).
- Package logos that are glyph-only get a plate (white glyph gets the manifest's plate colour; a black glyph gets a light plate).
- Fallback is a theme plate with the first letter (in the page). A theme may set `--ag-icon-style`: `native` (as is), `plate` (every icon on a plate), `mono` (grayscale plus a tint via `mix-blend-mode`).

Ran (`test_shell_icons.py`, 9 programs on this machine):

```
cache: ChatGPT.exe first 123.3 ms, second 11.9 ms; files on disk: 1
exe icons with alpha: 9 of 9 programs
window's own icon (WM_GETICON / class icon): 16 of 16 windows
saved evidence\shell\icons-sheet.png (28 icons on light and dark)
```

## How the bars talk to `wm.*` and the theme

- Windows: `wm.windows` first (rows with exe, title, state, focused, key); if it refuses (WM off), `window.desktop` + `window.list`, with native `window.activate handle=` and `do=close`.
  Bare exe paths in the WM's icon field are normalised to `exe:`; windows of the shell itself and Edge shell hosts are filtered with `window.list`.
- Pressing a dock icon: not running starts it (`window.launch`); not in front focuses (`wm.focus`); in front minimises (`wm.minimise`); minimised restores (`wm.restore`).
  The dock window takes focus when clicked, so the dock remembers the previous front app (`Dock.state.lastFront`).
- Theme: `Theme` loads `/desk/theme.css` (or `/theme.css`, or `?theme=<url>`, `?look=<slug>`, else the stand-in), and reloads on `theme.changed`. Pages never hard-code a colour.

## Proof (ran): `shell_proof.py all`, hidden and headless

Output in `evidence/shell/proof-output.txt`. As printed:

```
full screen x6: 3840x2160 composites (top bar, dock and desktop layer; 3 fake app windows in gapped places) in real:{seabright-day, dusk, night-metal, ink-landscape} and standin:{seabright-day, dusk}
popovers: 24 images (launcher, app menu, calendar, notifications, media, quick settings, JEFF, off armed, dock menu, dock preview, dock launcher)
dock real:seabright-day with 3 / 8 / 16 running apps: 10 / 15 / 23 items, pill 631 / 876 / 1268 x 52 css px, reserve 72 css px
dock real:dusk with 3 / 8 / 16: 10 / 15 / 23 items, pill 679 / 944 / 1368 x 56, reserve 84
dock real:night-metal with 3 / 8 / 16: 10 / 15 / 23 items, pill 535 / 740 / 1068 x 44, reserve 68
dock real:ink-landscape with 3 / 8 / 16: 10 / 15 / 23 items, pill 559 / 774 / 1118 x 46, reserve 70
keyboard and screen reader: [top] 12 landmarks and controls, 0 without a name; [dock] 18 landmarks and controls, 0 without a name
  top: Tab enters the toolbar, ArrowRight walks 8 controls, Enter opens the launcher (focus in the search field), typing filters it, Escape returns focus to the launcher
  dock: ArrowRight walks 17 controls; one more Tab leaves the toolbar (one tab stop); the Menu key opens an item's menu; Escape returns focus to the item
interaction, window manager answering: 10 checks ok (focus, minimise, restore, launch, middle click, right-click menu, pin, close all, hover preview, preview closes)
interaction, window manager off: 2 checks ok (window.activate fallback; menu has no pin-in-place, but windows, new window, keep in dock and close)
top bar: 5 checks ok (off needs two presses, wm.mode off then off window, media.play, quick-settings switch writes show_cpu, an optional reading appears only after the setting)
interaction: 17 of 17 checks passed
```

Screenshots, all in `evidence/shell/`: `full-real-*.png`, `full-standin-*.png`, `pop-real-<look>-<popover>.png`, `dock-real-<look>-{3,8,16}.png`,
`icons-sheet.png`, `spike-window-*.png`, `a11y-report.txt`. Every image was looked at. Fixed along the way: ink wallpaper rendering flat (invalid `background` shorthand and an unescaped `#` in a data URI),
quick-settings row order and wrapped network text, a stretched icon in the preview tile, an autofocus ring after pointer open, and the dock ring notch above.

Existing tests, `python -m unittest test_kdesk test_sysread test_shell_icons test_window_activation test_widgets` from this directory (ran):

```
Ran 48 tests in 48.688s
FAILED (errors=1)
ERROR: test_kits_copy_code_without_activation_or_grants (test_widgets.WidgetsTest) ... IndexError: list index out of range  (d.say('kit '+d.k.place)['made'][0])
```

47 pass. The one error is in the `kit` word, which lives in `research/kernel-lab/kernel/kits.py`; that file has another job's uncommitted edit (git shows it modified).
I did not touch it, and I could not check it against `HEAD` without changing git state, so "pre-existing" is an inference. `test_widget_native`, `test_widget_overlay`,
`test_stream_windows`, `test_pixel_guy` were not run (they do not exercise files I changed).

Not verified by any of this: DWM thumbnails (they cannot be seen on a hidden desktop), the AppBar strips under real Explorer, hit-testing of the real region windows,
the desktop layer over real icons, and real 150% DPI scaling beyond a 3840x2160 @1.5 device emulation in headless Edge.

## Live rollout, for Claude (with Alex present)

1. **Restart the window host** so it loads the edited `kd_window.py`, `kdesk.py`, `native_shell.py`. Until then nothing in the shell works, and the old process is unaffected.
   The edits are additive; the old taskbar path is unchanged while no shell row exists.
2. Run `window.shell on` (one act; `undo` or `window.shell off` restores the old bars). It forgets the legacy top bar and taskbar rows and makes three windows.
   Say first what will appear: a slim bar at the top, a pill at the bottom centre, and the desktop layer covering the screen under every app.
3. Verify live, in this order: the AppBar strips (maximised windows stop at the bar and the dock strip); the region corners (clicks at a corner reach the app behind);
   hit-testing over popovers; DWM hover thumbnails; the dock marks against real windows; that the desktop layer sits *under* every app and the loop keeps it there.
4. Optional: try `AGORA_DESKTOP_LAYER=workerw` to put the layer under Explorer's icons instead of over them. Unverified on 24H2; keep the off switch (unset it and restart).
5. The WM must exclude the shell's own windows (`edge`/`layer` rows) from its tiling, and the taskbar guard must not re-create the legacy taskbar while `shell-*` rows exist.
   I made the guard skip, but the guard is in the running process.
6. Off switch: the top bar's power button (two presses: `wm.mode off`, then `off window`), or `window.shell off`.

## Not done

- Live verification of everything under "Not verified" above.
- WorkerW on 24H2. Popover and dock shadows (a region cannot carry one).
- `wm.title` (live titles and the hover preview's text) and a hwnd on `wm.windows` rows: the preview falls back to the row title and placeholder art, and DWM thumbnails need a numeric hwnd.
- Real sound volume write (the slider is read-only without a word), network and battery detail pages beyond the readings shown.
- A notifications word (the bell reads `rows notification` only) and a presence word for JEFF.
- A theme-picker entry in the bar (the Appearance app is the way in). Theme-sharing itself is the theme builder's job; the shell only consumes `--ag-*`.
- Multi-monitor (one monitor assumed, as Alex's).

## Rough spots (source edits and the world-level word that was missing)

Post these on the Rough spots note (f747); I did not write to the live world.

1. `kd_window.py` `SHELL_VIEWS`, `AppBar.resize`, `PageApi.layout/thumbs`: a window needs to say its own shape and reserved strip. Missing word: `window.shape <rects>` and `window.reserve <px>`, written by a page to its own window.
2. `window.shell on|off`: a bar set is three window things made together. Missing word: a general *bundle* (`make` a named group; `forget` a named group in one act).
3. `kdesk.py` `/desk/icon`: an icon is not a world thing. Missing word: `icon <ref> [size]` that returns bytes through the door, so a page needs no route.
4. `native_shell.py` `ref=` on window rows and `do=close`: the WM's rows have no stable ref and no per-window close. Missing words: `wm.windows` rows with `ref`, `hwnd` and `wm.close` that names the native window the same way.
5. `wm.title <key>`: live titles for a preview.
6. A `system.volume <0..100>` write, a notification word, a presence word (see Not done).
7. Theme compiler: `--ag-icon-style`, `--ag-island-opacity`, `--ag-island-outline`; the `--ag-border` colour/width collision; `--ag-wallpaper-dim` as a colour.
