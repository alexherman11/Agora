> Research by Claude (researcher), 26 October 2026, for the coordinator's build commissions. Read-only: nothing installed or run from outside, no Windows setting changed, the live desktop (127.0.0.1:8810) not touched, no git state changed.
>
> Every claim is labelled **read** (primary source named), **ran** (executed here, output quoted) or **imagined** (inference or design). I did not see Alex's three inspiration photos; I work from his description of them. For reading I fetched komorebi's `master` source (v0.1.42 in `Cargo.toml`) and a few other repos as text into the session scratchpad; none of it was built or executed, and none is in this repository.

# Agora window manager and bars: research

## 0. The answer in twelve lines

1. **Recommendation: (b) Agora's own window manager, built on a pure layout engine, over the same Win32 seams komorebi uses.** Komorebi is studied, not embedded or copied. Optional later: a komorebi adapter for people who want tiling.
2. **Licence (read, LICENSE.md): personal use only.** Alex may run komorebi for himself. Nobody may distribute it or a work based on it, and Agora cannot ship it, wrap it in an installer or copy its code into a distributed Agora. Commercial use (work) is not permitted. Details in 1.9.
3. **None of Alex's headline behaviours exist in komorebi** (free non-overlapping placement, minimise-on-full, live push-aside drag, pins). Komorebi tiles on a grid of containers and reacts to a drag *on release* by swapping. Its floating layer overlaps. So (a) would still need Agora's own engine for everything he asked for.
4. **Agora already has most of the Win32 layer** (wm.py, kd_window.py, native_shell.py, taskbar_guard.py, the hidden-desktop sandbox). What is missing is event hooks (it polls), DWM styling, alpha icons, a live-drag solver, and a global theme.
5. **Komorebi's quirk knowledge is the valuable part**, and much of it is reusable as data: the `komorebi-application-specific-configuration` repo is **MIT** (227 entries) and `windows-icons` is **MIT**.
6. **Do not use `Cloak` to hide windows** in Agora's minimise-on-full: komorebi's own source says cloaking suspends Chromium/Electron renderers (Claude, Discord, Spotify and ChatGPT are running on this PC; they are probably Electron, but I did not map their window classes). Use real minimise.
7. **Theme:** one `theme` thing, base24-shaped palette plus semantic roles plus shape/type/motion/window/wallpaper sections, compiled to CSS variables for every painter and to a small native sheet for DWM borders, corners and gaps. Today Agora has three unrelated token sets.
8. **Sharing:** Agora's kit mechanism (`kit` / `take bundle=`) already carries `style` definitions between worlds; a theme can ride it.
9. **Safety:** shadow mode first (compute, log, move nothing), a separate watchdog process that owns the panic hotkey and restores positions, and tests on a hidden desktop plus a pure simulator. Komorebi's `stop` does **not** restore window positions.
10. **Komorebi changes a system setting on its own** (`ForegroundLockTimeout`, session-only), and the repo's current taskbar guard changes Explorer's auto-hide state (restored on exit). Both need Alex's say-so.
11. **Alex's PC is clean for komorebi's MDM check** (ran, 1.9).
12. Open questions are in section 8; the three that block building are what "minimise others" means, what "pin" means, and manage-everything versus adopt-by-key.

---

## 1. Komorebi as it really is

### 1.1 Snapshot

| Fact | Value | How known |
|---|---|---|
| Latest release | v0.1.41, 2026-05-03; x86_64 zip 28.0 MB, x86_64 msi 28.2 MB (aarch64 also) | **ran** (GitHub API: `releases/latest`) |
| Repo | 15,317 stars, pushed 2026-10-25, default branch `master`, licence reported by GitHub as "other" | **ran** (GitHub API) |
| Crates | `komorebi` (WM), `komorebic` (CLI), `komorebic-no-console`, `komorebi-client` (Rust IPC crate), `komorebi-bar`, `komorebi-gui`, `komorebi-layouts`, `komorebi-themes`, `komorebi-shortcuts` | **read** (Cargo.toml `[workspace]`) |
| Size of the core | `window_manager.rs` 217 KB, `process_command.rs` 111 KB, `workspace.rs` 98 KB, `static_config.rs` 93 KB, `process_event.rs` 50 KB, `windows_api.rs` 55 KB | **ran** (git tree API sizes) |
| Related, separate | `whkd` (hotkey daemon, also Komorebi-licensed), `komorebi-application-specific-configuration` (MIT), `awesome-komorebi` (CC0 list) | **ran** (API licence fields) |

### 1.2 How it manages windows through Win32 (all **read**, `komorebi/src/`)

| Concern | What komorebi does | File |
|---|---|---|
| Seeing windows | One thread calls `SetWinEventHook(EVENT_MIN, EVENT_MAX, ... WINEVENT_OUTOFCONTEXT \| WINEVENT_SKIPOWNPROCESS)` and pumps messages. Events go into a bounded channel (20). No DLL injection. | `winevent_listener.rs` |
| Event model | Raw WinEvents become 14 `WindowManagerEvent`s: Destroy, FocusChange, Hide, Cloak, Minimize, Show, Uncloak, MoveResizeStart, MoveResizeEnd, MouseCapture, Manage, Unmanage, Raise, TitleUpdate. | `window_manager_event.rs` |
| Which windows count | `window_is_eligible`: needs `WS_CAPTION` and `WS_EX_WINDOWEDGE`, no `WS_EX_DLGMODALFRAME`, no `WS_EX_LAYERED` unless whitelisted (Steam is built in), ignore/manage/float rules, a permanent-ignore class list. Separately, the border logic skips `WS_CHILD`, `WS_EX_TOOLWINDOW` and `WS_EX_NOACTIVATE` windows. | `window.rs` 1098-1250, `windows_callbacks.rs` |
| Cloaked / UWP | Cloaked windows are skipped unless the event is Hide/Cloak. A built-in "tray and multi-window" list (explorer, firefox, chrome, idea64, ApplicationFrameHost, steam) handles apps whose windows hide instead of closing. Firefox and IntelliJ get a "name-change on launch" workaround because they send no Show event. | `lib.rs` 81-135, `window_manager_event.rs` |
| Placing a window | `SetWindowPos` with `NOACTIVATE \| NOSENDCHANGING \| NOCOPYBITS \| FRAMECHANGED`, optional `ASYNCWINDOWPOS` (so a hung app cannot block the WM), `HWND_TOP` and never `TOPMOST`. | `windows_api.rs` 485-540 |
| Invisible borders | Measures the gap between `GetWindowRect` and `DWMWA_EXTENDED_FRAME_BOUNDS` and adds it to every placement (`shadow_rect`). | `windows_api.rs` 765-797 |
| DPI | Per-monitor awareness set at start; the code has a TODO about scaling rects. | `main.rs` 223, `windows_api.rs` 773 |
| Focus | Sends a dummy `SendInput` mouse event first so `SetForegroundWindow` passes the foreground lock. At start it also sets `SPI_SETFOREGROUNDLOCKTIMEOUT` to 0 if non-zero (see 1.9). | `windows_api.rs` 698-722, 1162-1198, `main.rs` 254 |
| Hiding on workspace switch | Three modes: `Hide`, `Minimize`, `Cloak`. Cloak calls the undocumented `IApplicationView::SetCloak` COM interface. | `window.rs` 696-745, `com/` |
| Chromium trap | Comments in `window.rs`: Chromium/Electron (`Chrome_WidgetWin_`) renderers are suspended whenever the HWND reports any cloak, so its animation path keeps those windows cloaked at the start rect and only uncloaks at the end. | `window.rs` 209-226 |
| Orphans | A "reaper" thread finds windows that vanished without a Destroy event, removes them, and writes `komorebi.hwnd.json`. | `reaper.rs` |
| Monitors | A reconciliator handles hot-plug, DPI/resolution changes and power events. | `monitor_reconciliator/` |
| Virtual desktops | Reads `HKCU\...\Explorer\VirtualDesktops` to know the current virtual desktop. | `lib.rs` 287-330 |
| Min sizes, elevated windows | I searched every Rust file I fetched for "elevat", "admin", "min_size", "MINMAXINFO": **no hits**. Elevated windows (UIPI blocks a normal process from moving them) and apps that refuse to shrink are not handled in code; users handle them with ignore rules. | grep over fetched files |
| Full screen / games | No game logic found. Monocle and "maximize" are WM modes, not game detection. | grep |
| Mouse | Optional focus-follows-mouse through a low-level input loop (`winput`), or Windows' own `SPI_SETACTIVEWINDOWTRACKING`. | `process_movement.rs`, `windows_api.rs` 1200-1232 |
| Wallpaper | `IDesktopWallpaper::SetWallpaper` per monitor or workspace. **This changes the system wallpaper.** | `windows_api.rs` 1484-1530 |

### 1.3 Borders

**Read** (`border_manager/border.rs`, `windows_api.rs` 1298-1320): komorebi's default border is a separate **top-level overlay window per managed window** (`WS_EX_TOOLWINDOW | WS_EX_TOPMOST | WS_EX_NOACTIVATE`), drawn with Direct2D, with rounded or square style, width and offset. The WinEvent hook forwards `EVENT_OBJECT_LOCATIONCHANGE` and `DESTROY` to the border window so it tracks the target. The alternative `BorderImplementation::Windows` uses `DwmSetWindowAttribute(DWMWA_BORDER_COLOR)` and `DWMWA_WINDOW_CORNER_PREFERENCE`, which is a thin system border on Windows 11 (build 22000+). The example config calls the overlay border "buggy" (read, docs example-configurations).

### 1.4 IPC (all **read**)

| Channel | Mechanism | Notes |
|---|---|---|
| Commands | A Unix-domain socket at `%LOCALAPPDATA%\komorebi\komorebi.sock`. One JSON `SocketMessage` per line (batches allowed). `komorebi-client::send_message`, `send_batch`, `send_query`. | `komorebi-client/src/lib.rs` |
| Message set | Over 200 variants: focus/move/resize/stack/promote/lock/float/monocle/maximize, workspaces, layouts, padding, borders, `Theme(Box<KomorebiTheme>)`, `Animation*`, `Stackbar*`, `WorkAreaOffset`, `Save/Load`, `ApplyState(State)`, `Stop`, `StopIgnoreRestore`, `State`, `GlobalState`, `VisibleWindows`, `MonitorInformation`, `Query(StateQuery)`. | `core/mod.rs` |
| State queries | `State` returns the whole monitor/workspace/container/window tree as JSON. | `process_command.rs` |
| Event stream | The **subscriber creates the socket** in `%LOCALAPPDATA%\komorebi\` and then sends `AddSubscriberSocket(name)`; komorebi connects and pushes `Notification { event, state }` for each event (window events, socket messages, monitor and virtual-desktop notifications). Named-pipe variant: `AddSubscriberPipe(name)` connects to `\\.\pipe\<name>`. `SubscribeOptions` can limit to state-changing events. | `lib.rs` 334-400, `process_command.rs` 1985 |
| Schemas | `SocketSchema`, `NotificationSchema`, `StaticConfigSchema` and `schema.json` / `schema.bar.json` (140 KB / 280 KB) ship in the repo. | `core/mod.rs`, tree listing |
| Config | `komorebi.json` (static config) in `%USERPROFILE%` or `$KOMOREBI_CONFIG_HOME`; `applications.json` beside it; `komorebi.bar.json`; data and sockets in `%LOCALAPPDATA%\komorebi`. | `lib.rs` 200-213, docs |

This is a good IPC: typed, schema-published, event stream carries the full state. If Agora ever drove komorebi (option a), a ~200-line Python client would be enough (**imagined**).

### 1.5 Layouts and Alex's behaviours (**read**: `komorebi-layouts/`, `workspace.rs`, `process_event.rs`)

Built-in layouts: BSP, Columns, Rows, VerticalStack, HorizontalStack, UltrawideVerticalStack, RightMainVerticalStack, Grid, and a new **Scrolling** layout. Custom layouts are JSON/YAML lists of columns (primary/secondary/tertiary with width ratios). Workspaces also have: a **floating layer** (a second, non-tiled layer toggled with `ToggleWorkspaceLayer`), `monocle` (one container full), `maximize`, per-layout padding (`container_padding`, `workspace_padding`, `border_offset`), `work_area_offset`, a **stackbar** (tabs when several windows share a container), `ToggleLock` (a locked container is kept in place), and `WindowContainerBehaviour::Create | Append` for new windows.

How each of Alex's wishes maps:

| Alex's behaviour | Komorebi | Evidence |
|---|---|---|
| Windows never overlap | Tiled layers never overlap. The floating layer does overlap. A window that refuses to shrink will overlap its neighbour (no min-size logic). | **read** |
| Tile freely / free placement | **No.** Everything is a tree or column list of containers. Custom layouts are columns with ratios, not free rectangles. | **read** |
| New window opens, others minimise | **No.** A new window `Create`s a container and every tile is re-laid out (`new_container_for_window`, `process_event.rs` 565-600), or `Append`s into a stack. Nothing minimises. | **read** |
| "Fill the space if it's full already" | Closest: Scrolling layout (new window opens beside the focused one, view scrolls) or monocle. | **read** (layout enum), partly **imagined** |
| Drag pushes neighbours aside, live | **No.** On `MoveResizeStart` it raises the window and stores a pending op; on `MoveResizeEnd` it either **swaps** with the container under the cursor (`Create`), **appends** into it (`Append`), or turns the drag into resize ops. Neighbours do not move during the drag. | **read** `process_event.rs` 647-870 |
| Pinned to the screen | Nearest: `ToggleLock` (container keeps its slot), floating layer, monocle. No "pin to all workspaces". | **read** |
| Resize from any corner | The OS frame does it. Komorebi turns the result into resize deltas per edge on release. | **read** |

### 1.6 Quirks it handles, and what that tells us

Handled: cloaked and UWP hosts, windows that hide instead of close, apps with no Show event, layered windows, the invisible shadow border, hung apps (async SetWindowPos), the foreground lock, Chromium cloak starvation, multi-monitor hot-plug and DPI, orphan windows, WSL2 GUI apps, slow apps (a per-app sleep), apps whose borders overflow. The per-app knowledge is in the separate `applications.json`: **227 entries** (**ran**, counted from the file): `tray_and_multi_window` ×121, `ignore` ×110, `object_name_change` ×24, `floating` ×19, `manage` ×15, `layered` ×10, `slow_application` ×4.

Not handled (by absence in code): elevated windows, minimum sizes, game/full-screen detection, restoring positions on exit.

### 1.7 Animation

**Read** (`animation/`, `window.rs`): optional move/transparency animations, with "ghost" windows (DWM thumbnails) so the real window moves once while a picture animates, and the Chromium special case above. Takeaway: animating other programs' windows is the hardest part of a WM; it needs per-toolkit workarounds.

### 1.8 komorebi-bar (egui)

**Read** (`komorebi-bar/Cargo.toml`, `src/main.rs`, `config.rs`, `widgets/`):

- **Built with** `eframe`/`egui` 0.33 (Rust, GPU-drawn), undecorated transparent viewport, hidden from the taskbar, hot-reloading `komorebi.bar.json` (`hotwatch`). Icons by `egui-phosphor`, window icons by the MIT `windows-icons` crate, tray by the `systray-util` crate.
- **Space reservation:** it does not register an AppBar. It tells komorebi to shrink the monitor's work area (`SocketMessage::MonitorWorkAreaOffset`), so **non-komorebi windows (a user-maximised one) can cover it** (**read**, `main.rs` 296-306; the AppBar part is **imagined** from absence, since I found no `SHAppBarMessage` use in the bar).
- **Config schema** (`KomobarConfig`): `height` (default 50), `padding`, `margin`, `position{start,end}`, `frame`, `monitor`, `font_family`, `font_size` (12.5), `icon_scale` (1.4), `max_label_width`, `theme`, `transparency_alpha` (200 of 255), `widget_spacing` (10), `grouping`, `mouse`, and `left_widgets`, `center_widgets`, `right_widgets`.
- **Widgets (13 types):** Applications (launcher buttons, icon extracted from the exe), Battery, Cpu, Date, Keyboard (layout language), **Komorebi** (workspaces, layout, workspace-layer, focused window with icon, locked container, configuration switcher), Media, Memory, Network, Storage, Systray, Time (with time zones), Update.
- **Look (from config, not from a picture):** a translucent strip, widgets in rounded groups, theme-coloured, icon + short label, workspaces as numbers/dots.

### 1.9 Theming and the licence

**Theming (read, `komorebi-themes/src/lib.rs`, `theme_manager.rs`, `bar.rs` 1388, `static_config.rs` 194-207).**

- One `theme` key in `komorebi.json`: `palette` = `Catppuccin` | `Base16` (any named base16 scheme from the `base16-egui-themes` crate) | `Custom` (16 explicit colours, base_00..base_0f).
- It names which base slot colours which window state: `single_border` (default Base0D), `stack_border` (Base0B), `monocle_border` (Base0F), `floating_border`, `unfocused_border`, `unfocused_locked_border`, stackbar text and background, and `bar_accent`.
- It is **pushed live**: `SocketMessage::Theme(...)` goes to the theme manager, which recolours borders and stackbars, and the bar, subscribed to the same stream, adopts it (`bar.rs` 1388, `From<KomorebiTheme> for KomobarTheme`). So **one message recolours borders and bar together**. This is the model Alex's "works across the system" wants.
- **Wallpaper to palette:** a workspace/monitor `wallpaper { path, generate_theme, theme_options (Light|Dark) }` generates a base16 palette from the image with the `flavours` crate and applies it. That is exactly the "ink landscape" rice mechanic.
- Limits: colours only. Gaps/padding, corner style and fonts are separate settings, not part of the theme.

**Licence (read, `LICENSE.md` fetched raw, 3,735 bytes).** "Komorebi License, Version 2.0.0", a fork of PolyForm Strict 1.0.0. Key clauses, verbatim:

- *Copyright License:* "...for any permitted purpose. However, you may only distribute the source code of the software according to the Distribution License, you may only make changes according to the Changes License, and you may not otherwise distribute the software or new works based on the software."
- *Distribution License:* "...to distribute copies of the source code of the software. Your license to distribute covers distributing the source code of the software with changes permitted by the Changes License."
- *Changes License:* "...to make changes for any permitted purpose."
- *Personal Uses:* "Personal use for research, experiment, and testing for the benefit of public knowledge, personal study, private entertainment, hobby projects, amateur pursuits, or religious observance, without any anticipated commercial application, is use for a permitted purpose."
- *No Other Rights:* "These terms do not allow you to sublicense or transfer any of your licenses to anyone else..."
- *Violations:* licences can continue only if you "come into full compliance ... within 32 days of receiving notice".
- README (read): free "for personal use other than redistribution, or distribution of new works (i.e. hard-forks)"; "does not permit any kind of commercial use (i.e. using komorebi at work)"; a paid Individual Commercial Use License exists for work. Forks are fine "for personal use or for integration back upstream via pull requests".

What that means for Agora (my reading, **not legal advice**):

| Action | Allowed? |
|---|---|
| Alex runs komorebi on his own PC for personal use | Yes (Personal Uses) |
| Alex modifies it for himself | Yes (Changes License) |
| Agora runs/controls komorebi over IPC on Alex's PC | Yes, it is Alex's personal use; IPC is not distribution |
| Agora **bundles** komorebi binaries or an installer, or hosts them | **No** ("may not otherwise distribute the software") |
| Agora copies komorebi code into itself and the combined Agora is shared with a neighbourhood | **No** (a "new work based on the software" that is distributed) |
| Neighbours each install komorebi from upstream and enable an Agora adapter | Probably yes for each person's personal/hobby use, but a community or organisation using it is a grey area ("without any anticipated commercial application"). Ask the author before relying on it. |
| Anyone uses it "at work" | No without a paid individual licence |
| Reuse the **ideas, API names, behaviours** described here | Yes; none is the code. Work from Microsoft's docs and this report, not from the source. |
| Reuse the MIT-licensed `applications.json` and `windows-icons` | Yes, with the MIT notice kept |

**Two behaviours to flag to Alex** (both **read**): (1) at startup komorebi may call `SystemParametersInfo(SPI_SETFOREGROUNDLOCKTIMEOUT, 0)`, a session-lifetime system setting (no `SPIF_UPDATEINIFILE`, so not persisted); (2) `komorebic enable-autostart` writes `komorebi.lnk` into the Startup folder (docs), and the install guide recommends enabling "turn off all unnecessary animations" and, for long paths, writing `HKLM\...\LongPathsEnabled` as administrator.

**MDM splash:** the README says a splash "intended for corporate users" appears on MDM-enrolled devices; `splash.rs` runs `dsregcmd /status` and looks for `WorkspaceTenantName`, and checks a licence only if an `icul` email file exists. **Ran** on this PC: `AzureAdJoined : NO`, `DomainJoined : NO`, `WorkplaceJoined : NO`, no `WorkspaceTenantName` line. So the check would not trigger today. If Alex later adds his Cal Poly account as a Work-or-school account it might.

### 1.10 What installing would involve (do not do; for Claude to ask Alex)

| Item | Detail | How known |
|---|---|---|
| Source | `scoop bucket add extras; scoop install komorebi whkd`, or `winget install LGUG2Z.komorebi` and `winget install LGUG2Z.whkd`, or the MSI/zip from GitHub (28 MB each). Building needs Rust and Visual Studio build tools. | **read** docs/installation |
| Files | `komorebi.exe`, `komorebic.exe`, `komorebi-bar.exe` (and `whkd`, a separate hotkey daemon with the same licence). `%USERPROFILE%\komorebi.json`, `applications.json`, `.config\whkdrc` (created by `komorebic quickstart`), logs and sockets in `%LOCALAPPDATA%\komorebi\`. | **read** docs |
| Start | `komorebic start --whkd --bar`; autostart via `komorebic enable-autostart` (a Startup-folder shortcut). | **read** docs |
| System changes | Optional animations setting; optional `LongPathsEnabled` (HKLM, admin); the runtime foreground-lock-timeout change above; wallpaper changes only if configured; `whkd` registers its own global keys. | **read** |
| Undo | `komorebic stop --whkd --bar`; `scoop uninstall komorebi whkd`; delete the files above. | **read** docs |
| Not verified | Whether Windows 11 Home needs anything extra; I did not install it. | not run |

---

## 2. Agora today (all **read** unless marked)

### 2.1 What exists for windows

| Piece | What it is | Notes |
|---|---|---|
| `kernel-desktop/kd_window.py` (893 lines) | The live desktop's window module. Windows are world things (`kind=window`), the screen follows the world level-triggered. WebView2 (pywebview) frameless windows; AppBars via `SHAppBarMessage` (`ABM_NEW/QUERYPOS/SETPOS`); full-screen step-back by polling the foreground window every 0.5 s; hand-drag recorded back into the world after the window rests 1 s (`watch_drags`, 0.5 s poll). Fixed `to=` spots with a 24 px gap (left, right, big, quadrants). | Only Agora's own windows are moved. Other programs' windows are listed as boxes and program names, never titles (`window.list all`). |
| `kernel-desktop/native_shell.py` | Windows task rows: `EnumWindows` filter (visible, no owner, not toolwindow, titled, not cloaked), `activate` (minimise if front, else restore + `SetForegroundWindow`), Start through Ctrl+Esc `SendInput`, `ms-settings:` URIs. | Icons from here (below). |
| `kernel-desktop/icons.py` | **Real exe icons** via `SHGetFileInfoW` + `DrawIconEx` into a 32×32 DIB, pre-filled opaque warm white, returned as PNG data URLs, cached. Lucide 0.468.0 (ISC) outline icons vendored for Agora's own symbols. | 32 px at 150% is soft on a 4K screen; background is opaque white, not transparent (read comment: "Opaque warm white also handles legacy mask-only icons"). UWP windows (hosted by ApplicationFrameHost) would show the host's icon (**imagined**, not tested). |
| `kernel-desktop/taskbar_guard.py` | Independent lease process, launched via WMI outside the kernel's job. Saves Explorer's AppBar state to `state/taskbar-lease.json`, registers `HKCU\...\Run` "Agora taskbar recovery", sets Explorer to auto-hide and hides its taskbars, restores on owner death, release, or Explorer failure. | Changes the Windows taskbar's auto-hide state programmatically. Alex's own rule is that he toggles Windows settings. It is reversible and guarded; flag it. |
| `kernel-desktop/gaming_gate.py` (57 lines) | `reasons()`: process snapshot with a known-game list (9 titles) plus any exe name containing "game" except 8 helper names, plus "foreground window not a shell class and covers the primary monitor". Used by widget tests and renderer-recovery, **not** by the bars (they use their own full-screen poll). | Crude: name heuristics. A documented API exists for this (see 6.2). |
| `kdesk_on.py` / `kdesk_off.py` | Start detached (WMI, pythonw); stop the whole tree and verify the work area is given back. Start-menu shortcuts "Agora desktop on/off". | The off path is solid. |
| `wm.py` (933 lines, 14 Oct, a5052; `try_wm`, `keys_wm`, `measure_wm`, `wm_switch`, `test_wm_release`, `wm-dock/put.py`) | **An earlier window manager prototype.** A *layout lens* (`wm-strip`) is painted in an unseen headless Edge page; the painter reports each part's box; the host moves each real window to the box of the part keyed by its name. Keys (global, `RegisterHotKey`): slide the strip, pin, collapse to a "lesser lens", adopt the focused ordinary window (only on that key, one at a time), release, and Ctrl+Alt+Backspace = release everything. Adopted windows' `WINDOWPLACEMENT` is saved to `state/wm.json` before anything moves them. `--release-all` is a separate process that reads only that file, kills only processes whose pid **and** creation time **and** exe still match, and quarantines stale state files from before the last boot. The home base's dock icon starts and stops it (`host wm.start/stop`); the host watches its parent and puts everything back if it dies. Invisible borders are compensated (`frame_margins`). | **Ran** (the log `state/wm.log`, 32 recorded layout timings): min 25 ms, median 253 ms, max 2150 ms from key or edit to windows in place. Good for slides, **too slow for live dragging**. It polls; no WinEvent hooks anywhere in `research/` (grep for `SetWinEventHook` over `*.py` outside `.worktrees`: no files). Not wired to the kernel-desktop; it predates it. |
| `hud.py` (home base, Ctrl+Alt+J / bare Win tap via a `WH_KEYBOARD_LL` hook in `winkey.py`) | A summoned overlay with **live DWM thumbnails** of other programs' windows, and DWM-frost tried and dropped: "a see-through page over the system's acrylic or mica backdrop... never showed through (three ways...); the window drew solid" (ran 15 Oct per its docstring). | Relevant: system backdrop on WebView2 windows has already failed once. |
| `host.py` (10 Oct probe) | Borderless per-pixel-alpha windows pinned "top" or "bottom" (on the desktop under every app), click-through; arrange mode with Ctrl+Alt+L. | Proof that an Agora-owned background layer is feasible; its z-order trick was not examined here. |
| `sandbox_window.py` and the `test_sandbox_*` family | **Real windows on a hidden desktop** (`CreateDesktop`, never switched to), input by posted messages, and every verb measures Alex's foreground/focus/cursor before and after and says `alex: untouched`. | The testing rig the WM needs (section 6.5). |
| `web/` tiling host in the kernel (a13322; `proof/WEB-HOST.md`) | Browser tiling host: a person's split tree stored as a private `web-layout` thing, words `pane.split/close/move/focus/resize`, phone mode shows one pane. | The in-browser analogue; the **same** world words could later drive native windows (**imagined**). |
| Kits (`kit`, `take bundle=`; `proof/KITS.md`) | Gathers a group's verbs, lenses, styles, rules and kind declarations into a closed-schema, portable bundle that carries between worlds through ordinary doors. | The sharing channel for themes (section 5.5). |

### 2.2 What the screen looks like now (**read**: two evidence PNGs, `evidence/bars-v2-top.png`, `bars-v2-bottom.png`; both are hidden-fixture renders, not the live screen)

- Top bar: 2560×40 px render, a flat light strip; two small icons at the far left, and at the right a row of small rounded pills: music, skip, CPU 12%, memory 41%, network ↓1.2 KB/s, volume 35%, feed 2, calendar 10:55.
- Bottom bar: 2560×44 px render, flat, **left-aligned**; Start, Lines, world pins, then a run of real colour exe icons (File Explorer, Discord, Chrome, terminals, Python, Spotify…), clock, tray readings and a power icon at the right.
- So it works, but it is wide flat strips of small readings: the opposite of "centred dock, clean, no clutter".

### 2.3 What the three token systems are (the theming starting point)

| System | Where | Vocabulary | Reach |
|---|---|---|---|
| Lens style notes (lens.js) | e.g. `lenses/bars.style`, `tiles.style` | `token paper/card/ink/accent/warn/mark/sage/rose = #hex`, `token gap`, `token icon`, `token pill`, `token ramp`, `token text = ui 15/1.5`, derived `token line = ink at 18%`, plus `role X : on card, ink, text down, pad gap /2, corner gap, edge faint, hover accent at 8%` | The lens that names the style. Shared by name. |
| Host chrome CSS | `pages/kd.css`, `bars.css` | A hand-copied `:root{--paper,--card,--ink,--accent,--warn,--mark,--line,--faint,--quiet,--hush,--gap,--font,--mono}` and about 30 hard-coded hex colours in each of `kd.css` and `bars.css` (**ran**: `grep -o` counts) | Lines, Help, Thing, taskbar page, frame. Not connected to the lens style. |
| Component painter | `agora/painter/primitives.js` line 4, `painter.js` 119-184, `handles.py` | Default tokens `paper, card, ink, muted, accent, red, orange, blue, grey, rose, peach, sage, sky, lilac, small/medium/large/soft/round`; per-lens overrides by `make kind=part-style lens=<l> target=tokens ...` (also `personal=yes sees=me`); set as CSS variables on `:root`; motion tokens `motion-<name>`; safe font-family and spacing tokens | One lens at a time. The board's own `theme.js` is **generated** by replacing every hex with `--board-colour-0 ... -45` (`build_theme.py`): semantics are lost. |
| Widget bridge | `widgets.py` `theme()` | Reads only `paper|card|ink|accent` from a style by regex and passes them to a widget | Widgets only. |

Finding: no place-level or person-level theme exists; no role vocabulary is shared by the three painters/hosts; nothing reaches a native window.

---

## 3. Three ways to "adapt komorebi into Agora"

### (a) Run real komorebi as an engine; Agora draws bars and listens over IPC

How: Alex installs komorebi (his personal use). A new Agora module (`kd_komorebi.py`, in the module protocol) subscribes with `AddSubscriberSocket`, mirrors `State` into world readings (like `live.json`; not recorded), and offers words (`wm.layout`, `wm.focus`, `wm.float`, ...) that send `SocketMessage`s. Agora's top bar and dock replace `komorebi-bar` and Explorer's taskbar; Agora's AppBars reserve space (komorebi respects the monitor work area; **imagined**, since `win32-display-data`'s work-area source is not verified here) or it sends `MonitorWorkAreaOffset`. Theme: Agora sends `Theme(...)` with colours derived from the Agora theme.

| Alex's behaviour | (a) can do it? |
|---|---|
| No overlap | Yes inside a tiled layer; no for floating windows or windows that refuse to shrink |
| Tile freely / fill the space | Partly: Scrolling or Grid layouts. Not free rectangles |
| New window minimises others when full | No. Would be an Agora rule that sees `Show` events over IPC and sends `Minimize`/`ToggleMonocle`; races with komorebi's own re-tile (**imagined**) |
| Drag pushes neighbours aside, live | No (swap on release). Agora cannot intercept a drag inside komorebi |
| Pins | Partly: `ToggleLock`, floating layer. No pin-to-all |
| Resize from any corner | Yes (OS); komorebi converts to ratios on release |
| Gaps, borders, rounded look | Yes: container/workspace padding, overlay or DWM borders |

Pros: tiling, workspaces, monitors, hot-plug, quirks and per-app rules work today; ~1 week of adapter work (**imagined**). Cons: **cannot ship** (licence); half of Alex's list is outside its model, so Agora would fight it; two WMs' state to reconcile; MDM splash risk; komorebi's `stop` does not restore positions; foreground-lock setting changes; it is a second large Rust program Alex must install and keep updated; the community cannot get it from Agora.

### (b) Agora's own window manager over the same Win32 seams

How: three layers (**imagined**, designed here from the code I read):

1. **Layout engine** (pure, no Win32): `layout(state, event) -> placements`. State: work area, gaps, windows `{id, preferred size, min size (learned), pinned, last_used, mode}`. Events: open, close, minimise, focus, drag-start/move/end, resize, pin, work-area-change. Pure Python, deterministic, serialisable; testable with a simulator and property tests (no overlap, inside work area, pinned unmoved, idempotent, bounded motion).
2. **Win32 host** (thin): WinEvent hook feed (same events komorebi subscribes to), `SetWindowPos` with frame compensation and `ASYNCWINDOWPOS`, real minimise/restore, DWM attributes, AppBars, `WINDOWPLACEMENT` save/restore, an eligibility filter seeded from MIT app rules.
3. **World** holds intent only (pins, per-app rules, mode, theme), never per-frame geometry. wm.py's "layout is a lens" was elegant but measured 25–2150 ms (ran, above): fine for "arrange" commands, not for drag.

| Alex's behaviour | How (b) does it |
|---|---|
| No overlap | The engine's invariant. Obstacles it cannot move (elevated windows, windows that refuse to shrink) are treated as fixed rectangles. After each `SetWindowPos`, read back the real rect (`DWMWA_EXTENDED_FRAME_BOUNDS`) and re-solve (**imagined**; komorebi does no read-back) |
| Tile freely | Free-rectangle packing instead of a tree: place a new window in the best free rectangle that fits its preferred size; split free space guillotine-style |
| New window minimises others when full | If no free rect holds `min size`, minimise least-recently-used unpinned windows until one does (real minimise, **not** cloak). If "fill" is wanted when nothing fits, the new window takes the whole free area |
| Drag pushes neighbours aside | Minimum-translation push along the axis of least overlap, cascading, walls and pins immovable; if a cascade cannot resolve, shrink to min size, then minimise the LRU, else clamp the drag. **v1: ghost preview** (an Agora layered click-through overlay shows the resulting layout) and commit on release, avoiding live moves of GPU/Chromium windows; **v2: live**, if measured smooth on a hidden desktop. Live needs the dragged window's rect at ~60 Hz (`EVENT_OBJECT_LOCATIONCHANGE`, which komorebi already uses for borders, or polling) |
| Pins | A pin is an immovable obstacle everything else arranges around (Alex, 12 Oct: "pinning something so everything else arranges around it"); optionally also stays on every workspace |
| Resize from any corner | Native for foreign windows (frame hit-test). Agora's frameless windows need their own `WM_NCHITTEST` corners (kd_window currently has a title strip and `PageApi.resize`). A resize is a push too |
| Gaps, rounded, coloured borders | Gaps are the engine's; corner preference and border colour through `DwmSetWindowAttribute` (Win11 22000+) on windows Agora places; or Agora-drawn overlays as komorebi does |
| Wallpaper visible | Gaps show it; no wallpaper change needed (6.4) |

Pros: exactly Alex's model; shippable and shareable (all new code, MIT/Apache-compatible inputs only); the engine can also drive the in-browser tiling host and Agora's own windows; builds on wm.py's tested release-all safety. Cons: you own every quirk komorebi has fixed over years (cloaked UWP, Firefox no-Show, layered windows, slow apps, hot-plug); more work (**imagined**: weeks, not days); live drag on arbitrary apps is unproven.

Mitigation for the quirks: seed ignore/manage/float rules from the MIT `applications.json` (227 apps), and ship in **shadow mode first** (6.5).

### (c) Hybrids

- **c1 (recommended shape):** (b) plus MIT data and ideas from komorebi. Also later an **adapter** that mirrors komorebi's state into Agora for people who already run it, using the existing `adapters` word. No distribution problem because the user installs komorebi themselves.
- **c2:** (a) for Alex now, (b) for everyone later. Cheapest for him this week, but he gets none of his own behaviours, and two engines would be thrown away.
- **c3:** zone-based (FancyZones-style, PowerToys is MIT): fixed zones, snap on drop. Not free packing and no push; it would deliver "tile" and "pin" but not the rest.

### Recommendation and what would change it

**Choose (b)/(c1).** Build in this order: pure engine and simulator; observe-only host (live window feed, no moves); arrange-on-open for adopted windows only; ghost-first drag; DWM styling; opt-in "manage all".

What would change my mind:
- Alex says plain tiling with gaps and workspaces is enough. Then (a) is the cheapest path for him personally (never shared).
- A hidden-desktop spike shows ghost or live push-aside is unworkable on Chromium/Electron windows (Alex's PC runs Claude, Discord, Spotify and ChatGPT, probably Electron, and the survey saw two `Chrome_WidgetWin_1` windows). Then reduce to "arrange on open and on release", which is closer to (a).
- The author grants permission to redistribute, or Agora stays personal. Then (a) loses its main objection.
- Evidence that elevated and refusing-to-shrink windows are common in Alex's daily use (the survey in 6.3 found one process I could not query out of 38 visible windows, so probably rare).

---

## 4. The bars

### 4.1 What the three look like and show

| | komorebi-bar | yasb | zebar |
|---|---|---|---|
| Built with | Rust, egui | Python, PySide (Qt), QSS-like CSS (**read**: `src/core/bar.py`, docs) | Native webviews; HTML+CSS+JS widgets, Rust backend; GPL-3.0 (**read**: GitHub page, licence API) |
| Space | work-area offset sent to komorebi | `Win32AppBar` (real AppBar), optional blur via `enable_blur`, rounded corners type | `dockToEdge{enabled, edge, windowMargin}` per preset |
| Default content | workspaces, layout, focused window with icon, media, net, cpu, mem, storage, battery, date/time, update, systray | about 50 widget modules: active_window, taskbar, windows_desktops, clock, media, volume, wifi, battery, cpu, memory, disk, gpu, weather, notifications, systray, power_menu, control_center, launchpad, quick_launch, pomodoro, todo, wallpapers, window_controls, claude_usage, codex_usage... | providers (audio, battery, cpu, date, disk, glazewm, host, ip, keyboard, komorebi, media, memory, network, systray, weather) rendered by your HTML |
| Style | `theme`, `transparency_alpha`, `grouping`, `padding` | `styles.css` with `.yasb-bar`, `.container-left/center/right`, "adaptive" style: a rail with "islands" per widget group, `-qproperty-islandradius`, `borderwidth`, `bordercolor` | any CSS |
| Shares | config files; `awesome-komorebi` list | Themes Manager (`yasb_themes.exe`), `yasb.dev` gallery, one-click install via a registered `yasb-themes://` URL protocol, paid encrypted "YASB Cloud" backup with public link (docs warn that a shared backup may hold API keys) | in-app marketplace of widget packs; `zpack.json`; `privileges.shellCommands` (allow-list of `program` + `argsRegex`) |

Not seen: I did not view Alex's photos, so I cannot say how closely these match them. The description he gave (slim top bar, gaps, one palette, wallpaper visible) is what the proposal below follows.

### 4.2 Proposed top bar (clean, clickable, useful)

One slim bar (about 36 logical px = 54 px at 150%, currently 60 px), full width, translucent, all readings as icons or short text; every element is a button that opens a small popover. All are Agora components painted by the painter in a bar slot, as the current top bar is.

| Zone | Widget | Click | Notes |
|---|---|---|---|
| Left | Agora mark | open the launcher / Lines | replaces Start for Agora things; Windows Start stays reachable by keyboard |
| Left | Space chips (only when more than one space/workspace) | switch | the home base already has `workspace <name>` verbs |
| Left | Focused app: icon + name | window menu: pin / minimise / close / send to space | replaces title text; never stores titles |
| Centre | Time and date | calendar and notifications popover | the only large text |
| Right | JEFF presence dot | open Conversation | status only |
| Right | Notifications (count badge) | inbox | `desktop/notification-inbox/` exists |
| Right | Media: icon, track in the tooltip | play/pause; right-click next | one widget, not two pills |
| Right | One status cluster: network, volume, battery | opens one quick-settings popover | replaces three pills |
| Right | Off (two-press) | stops the WM and bars | already exists |

Opt-in, not default: CPU, memory, network speed, feed count (all already one `make kind=widget` line).

### 4.3 Proposed bottom dock (centred, colour icons)

A floating rounded pill, centred, with a margin above the screen edge, so the wallpaper shows at both sides. From left to right: Agora mark; pinned apps (world `kind=button`/`pin` things with `path=`, which already exist); running apps that are not pinned, with a dot under the active one and a dimmed icon when minimised; Agora's own app windows; a separator; overview/show-desktop. Interactions: click = activate, or minimise if already front; middle-click = new window; right-click = that app's windows and pin/unpin; hover = a live DWM thumbnail (hud.py already draws thumbnails). No clock, no readings, no tray in it; those live in the top bar.

Implementation notes (**imagined**): an AppBar spans a whole edge, a centred pill does not. Use two windows: an invisible full-width reserve strip (the AppBar) and a pill-sized topmost no-activate window above it, centred. Per-pixel-alpha through WebView2 needs the controller's transparent background colour; the repo's pywebview colour-key transparency was already found broken after a move (README: the guy became a layered PIL window), so spike this before committing.

### 4.4 Colour icons for any window

| Source | Method | Status |
|---|---|---|
| Ordinary exe | `SHGetFileInfoW` today at 32 px on opaque white. Better: `IShellItemImageFactory.GetImage` at 64–256 px with alpha, or `ExtractIconEx` large icons, drawn onto a transparent 32-bit DIB | today **read**; better path **imagined** |
| The window's own icon | `WM_GETICON` (`ICON_BIG`), then class icon `GCLP_HICON` (Electron, Python, PWA windows set these) | **imagined** (komorebi-bar uses `windows-icons::get_icon_by_hwnd`, then by process id; **read**) |
| UWP / packaged apps | Windows are hosted by `ApplicationFrameHost.exe`, so take the child CoreWindow's process, find the package folder, read `AppxManifest.xml` → `VisualElements` → `Square44x44Logo`, pick the right scale file. That is what the MIT `windows-icons` crate does (`uwp_apps.rs`, **read**: first 80 lines, plus `DesktopShortcut.ico` shortcut). Alternative: resolve the AppUserModelID and ask the shell for `shell:AppsFolder\<AUMID>` (**imagined**) | mixed |
| Pinned by path | `path=` already on pins (README) | **read** |
| Agora apps | Each app thing carries `icon=` as a small colour SVG/PNG asset (kits would carry it); today only mono Lucide outlines exist | gap |
| Fallback | A theme-coloured rounded square with the first letter | **imagined** |

Rule: **icons keep their own colours by default**; a theme may add a plate (rounded square in a palette colour) or a mono tint as an option, because Alex wants icons that "represent what the things are".

---

## 5. Theming across the system

### 5.1 What exists to build on

- **Standard:** tinted-theming base16 (MIT, `tinted-theming/home` and `schemes`, **ran**: both MIT) has 16 slots: base00 background, base01 lighter background (status bars), base02 selection, base03 comments/invisibles, base04 dark foreground (status bars), base05 default foreground, base06 light foreground, base07 lightest, base08–0F accents (red, orange, yellow, green, cyan, blue, purple, brown) (**read**: styling.md). Base24 adds 8 slots (base10–17) "for full ANSI support in your terminals" (**read**: README); my recollection is that they are darker backgrounds plus bright variants (**imagined**, unverified). The README claims 70+ app templates (the official list I saw has 37) and 230+ schemes in the gallery (**read**). Scheme YAML: `system: "base16"`, `name`, `author`, `variant: "dark"`, `palette: {base00..base0F}` as `#hex` (**read**). Builders: Tinted Builder Rust (GPL-3.0, **ran**) and a Go builder; the template format is mustache (**imagined**; not in the page I fetched).
- **Komorebi** applies one theme to borders and bar live, and generates a palette from a wallpaper (1.9).
- **Catppuccin** (MIT) is the biggest curated family.
- **YASB/Zebar** show the sharing paths people actually use: a gallery with one-click install, and a marketplace.

### 5.2 What Windows exposes, and who it affects

| Mechanism | Affects | Changes Alex's system settings? | Min Windows | Source |
|---|---|---|---|---|
| `DwmSetWindowAttribute`: `DWMWA_BORDER_COLOR` (also `DWMWA_COLOR_NONE` to hide it), `DWMWA_WINDOW_CORNER_PREFERENCE`, `DWMWA_CAPTION_COLOR`, `DWMWA_TEXT_COLOR`, `DWMWA_USE_IMMERSIVE_DARK_MODE` | Per window. Komorebi sets border colour and corners on other programs' windows; the docs say "the app is responsible for changing the border color according to state changes" | No (per window, resets when the window closes; Agora should reset on release) | 11 build 22000 | **read** (MS Learn; komorebi `windows_api.rs`) |
| `DWMWA_SYSTEMBACKDROP_TYPE` (Mica/Acrylic/Tabbed) | Per window, "including behind the non-client area"; mainly for windows the app owns | No | build 22621 | **read** (MS Learn); but see hud.py's failed WebView2 attempt |
| `DWMWA_EXTENDED_FRAME_BOUNDS`, `DWMWA_CLOAKED` | Read-only queries | No | Vista+ | **read** |
| AppBar (`SHAppBarMessage`) | Shrinks the **work area** of the monitor for everyone while registered; the shell gives it back when the process ends (Agora measured 625 ms after a kill) | No (while running). Explorer's *own* auto-hide state is a setting | 95+ | **read** (MS Learn; kd_window README) |
| Agora's own windows (bars, dock, overlays, borders as overlays) | Only Agora's windows | No | any | **read** |
| Desktop background layer as an Agora window | Create a window under the icons by parenting to the `WorkerW` that appears behind `SHELLDLL_DefView` after sending Progman message `0x052C` | No (no wallpaper file changed), but forum reports disagree about Windows 11 24H2, and Alex's PC is build 26200 | any | **read** (search results only: community posts, not MS docs); needs a hidden-desktop spike |
| `IDesktopWallpaper::SetWallpaper` (komorebi's way) | Changes the user's wallpaper setting | **Yes** | 8+ | **read** (komorebi `set_wallpaper`) |
| Explorer's taskbar auto-hide / hiding it | Windows taskbar behaviour | **Yes** (reversible; Agora already does this with a recovery lease) | any | **read** (taskbar_guard) |
| System accent/dark mode registry values | Whole system | **Yes**, not needed | | |
| `SPI_SET*` calls (focus-follows-mouse, foreground lock) | Session-wide input behaviour | **Yes** | | **read** (komorebi) |
| Registering a URL protocol for one-click install (yasb does) | HKCU registry | **Yes** (small, user-level) | | **read** (yasb docs); do not do without asking |

Everything Agora needs for the look (bars, dock, gaps, borders, overlays) can be done **without changing a system setting**. The three that do (hiding Explorer, wallpaper, URL protocol) need Alex's approval.

### 5.3 Proposed portable theme: `agora-theme`

A theme is **one world thing** (`kind=theme`) that is also a closed-schema definition for kits. Sections (all optional except palette; missing values derive):

```
theme "Ink Landscape"
  meta      author, licence (default CC-BY-4.0 for look, never a font file), variant light|dark|both,
            preview image, tags, base16_slug (if derived)
  palette   base00..base0F required, base10..base17 optional (derived when absent; same hex format as tinted schemes)
  roles     bar, surface, raised, ink, ink-muted, accent, accent-ink, ok, warn, danger, info, border, focus, select, scrim
            (each defaults to a base slot: bar=base01, surface=base00, raised=base01, ink=base05, ink-muted=base04,
             accent=base0D, ok=base0B, warn=base09, danger=base08, info=base0C, border=base02, select=base02)
  type      ui, mono, display (family stacks with fallbacks), scale ratio, base size, weights, tracking
  shape     radius scale (none, small, medium, large, pill), border width, window gap inner/outer, bar height, dock size
  surface   bar opacity, window opacity, blur (none|soft|strong: approximated), shadow
  motion    durations, easing, spring, reduce-motion flag
  windows   border colour per state (focused, unfocused, pinned, floating, attention) given as roles,
            border width, corner preference (square|round|small-round), pinned marker
  icons     set (native-colour | line | filled), plate (none|square|round) and its colour rule, tint
  wallpaper asset ref(s), fit, per-space map, optional "derive palette from wallpaper"
  outside   opt-in targets: windows-terminal, vscode, ... each one a generated file, never auto-applied
```

Mapping to base16/base24: palette slots follow tinted-theming exactly, so any of the 230+ published schemes imports unchanged and any Agora theme exports to the 70+ community templates. Komorebi's state-to-slot defaults (focused Base0D, stack Base0B, monocle Base0F, **read**) are a precedent for the `windows` section. A theme with `derive from wallpaper` can use a palette generator (komorebi uses `flavours`; **read**), then show the result for the author to edit.

How it reaches things (all **imagined**, designed from section 2.3):

| Consumer | Receives | Mechanism |
|---|---|---|
| lens.js lenses and bars | `token`s: `paper=roles.surface`, `card=roles.raised`, `ink=roles.ink`, `accent=roles.accent`, `gap`, `text`, `ramp`, `pill`, plus stable `role` shorthands | The compiler emits a `style` note from the theme; lenses keep naming `style=<name>`, or inherit the place theme when they name none |
| Component painter | Tokens `paper, card, ink, muted, accent, red, orange, blue, ... small/medium/large/round`, motion tokens, font tokens | Emit the existing `part-style target=tokens` form at place or person scope (today per lens only) |
| Host chrome (`kd.css`, `bars.css`, `bar.html`) | The same CSS variables | Serve `/desk/theme.css` generated from the theme; delete the hand-copied `:root` and 30 hard-coded hexes per file |
| Widgets (JS) | the current four colours plus roles | extend `Widgets.theme()` |
| Native windows Agora places | border colour/width/corner preference, gap | A small JSON "native sheet" read by the window host; applied with `DwmSetWindowAttribute`; reset on release |
| Wallpaper | An asset drawn in Agora's own background window, or a gradient spec | no system change |
| Windows Terminal, VS Code, etc. | A generated colour scheme/settings snippet, shown to Alex, written only after he accepts | tinted-theming templates; a file per target |

### 5.4 What the painter already gives, and what is missing

Already: lens style tokens and roles, derived tokens (`ink at 18%`), personal overrides (`personal=yes sees=me`, `view-preference`), CSS-variable emission on `:root`, safe token validation that refuses CSS injection (`handles.py`: colours, measures, bounded numbers, plain font names), `look-view` readings, hot repaint on style change, kits carrying styles.

Missing:
1. A **place/person-level theme** that lenses inherit. Today tokens are per lens.
2. One **role vocabulary** shared by lens.js, the component painter, host CSS and widgets (three sets, section 2.3).
3. **Non-colour tokens** everywhere (gap, radius, type scale, motion exist only in some).
4. A **native bridge**: nothing carries a theme to DWM or to window gaps.
5. **Light/dark pairs** and system-follow.
6. **Assets in kits** (wallpaper, icons, fonts): the closed kit schema carries definitions, not files (**read** KITS.md; I did not find asset handling there).
7. Theme **validation and preview** before apply (a theme "try for 30 s, auto-revert" is the safe default for a stranger's theme).
8. The generated `--board-colour-N` style of `theme.js` must not be the pattern for shared themes.

### 5.5 How people share one

| Channel | How | Risk and fit |
|---|---|---|
| A kit | `kit <group>` holding the `theme` thing (and asset refs); `post` it on the community board; neighbours `take` it | The closed schema already carries styles and refuses executable configuration. Best fit. Needs asset support |
| A file | `agora-theme.json` (+ a folder of assets) in a folder or zip | Easy to attach and diff; import validates against the closed schema |
| A world thing | A theme note in a shared group, `origin={world, thing}` already recorded | Free provenance |
| A board post | The community board's post with the kit attached and a preview image | Discovery |
| A URL scheme (`agora://theme/...`) | one-click | Registry change; ask first |

Safety rules for strangers' themes (**imagined**): a theme is data only (no JS, no URLs fetched at apply time, fonts by name only); tokens go through the same validators that already refuse CSS injection; `outside` targets need an explicit per-target accept; licence and author shown; "try for 30 s" with auto-revert; never apply a wallpaper change to the system without a toggle.

---

## 6. Safety and off switches

### 6.1 Principles

Opt-in before opt-out; shadow before live; every effect has a named off; the panic path never depends on the thing that might be broken; nothing touches anything it cannot undo.

### 6.2 Games and full screen

- Today: `gaming_gate.py` (name heuristics plus "foreground covers the monitor") and each bar's own 0.5 s poll (the shell's `ABN_FULLSCREENAPP` "did not arrive" in a test, README).
- Add: `SHQueryUserNotificationState` (documented; reports `QUNS_BUSY`, `QUNS_RUNNING_D3D_FULL_SCREEN`, `QUNS_PRESENTATION_MODE`; **imagined**, from memory, not verified here) as the primary signal, the existing heuristics as backup, and a user-editable "never touch" list seeded from the MIT `applications.json`'s ignore entries.
- While gated: the WM processes no events, moves nothing, bars hide, hooks stay passive. Resume with a gentle re-layout. Avoid low-level input hooks while a game runs (**imagined**: anti-cheat dislikes them; `winkey.py` already installs a `WH_KEYBOARD_LL` hook and re-seats it every minute).

### 6.3 Elevated and unmanageable windows

- **Ran** (read-only survey of this PC, `scratchpad/survey_windows.py`; no titles read, nothing changed): `visible top-level windows: 38`; `alt-tab-like candidates ... 10`; `cloaked: 9 iconic: 8`; `elevation: Counter({'normal': 37, 'no-query-access(5)': 1})`; `dpi values: Counter({144: 38})`; candidate programs `windowsterminal.exe 3, chatgpt.exe 2, explorer.exe 2, claude.exe 1, discord.exe 1, spotify.exe 1`; `invisible border (l,t,r,b) of candidates: ((0,0,0,0), 2), ((9,0,9,9), 2)`; `monitors: 1 primary px: 3840 2160`; `work area: 0 60 3840 2094` (Agora's bars were running). One process could not be queried (access denied), which is how an elevated or protected process looks to a normal one (unverified which it was).
- Design (**imagined**): treat a window whose process token cannot be opened, or where `SetWindowPos` fails or does not change the rect, as **unmanageable**: never touch it, but treat its rectangle as a fixed obstacle in the layout. Detect elevation changes when a window's process restarts. Do not run Agora elevated; do not use UIAccess.

### 6.4 Put everything back

- Save `WINDOWPLACEMENT` (show state, normal rect, min/max points) for every window **before** the first move (wm.py does this, **read**), plus its process identity (pid + creation time + exe).
- On off: restore in reverse; skip a window whose process identity changed; report each left alone.
- Komorebi does not do this (it only un-hides, removes accents and re-adds title bars, **read**), so it cannot be the model.
- If DWM border colour or corner preference was set on a window, set `DWMWA_COLOR_DEFAULT` back on release. Per-window DWM changes die with the window anyway.

### 6.5 One hotkey, one click, and a watchdog

- Existing: Ctrl+Alt+Backspace (wm.py `RegisterHotKey`), the bottom bar's power icon (two presses), `off window`, `kdesk_off.py`, Start-menu "Agora desktop off". Ctrl+Alt+R is taken by another program; avoid Ctrl+Alt+Left/Right (windows-host-gotchas memory).
- Proposed: a tiny **independent watchdog process** (like `taskbar_guard.py`) that owns the panic hotkey, the lease file (placements + taskbar state), and a heartbeat from the WM. If the WM stops sending a heartbeat for ~3 s, or the hotkey is pressed, the watchdog runs release-all (windows, taskbar, AppBars) without the WM. The HKCU Run recovery entry already used for the taskbar covers a crash across sign-out. One hotkey and one click both end at the same release-all.
- One **mode switch** per level: `wm off` (stop moving windows, keep bars), `bars off`, `everything off`; each undoable in the world like `off window`.

### 6.6 Testing without visible windows (Alex's rule)

| Layer | What it tests | Visible? |
|---|---|---|
| L0 pure engine | Property tests over simulated windows: no overlap, in work area, pinned unmoved, push cascade terminates, minimise-LRU, idempotence, undo; fuzzed event sequences; replay of recorded real sessions. Deterministic, fast, no Win32 | Never |
| L1 Win32 layer on a **hidden desktop** | `sandbox_window.py` already creates `agora-sandbox-<name>` desktops (CreateDesktop, never switched to; "alex: untouched" before/after checks). Run the WM's Win32 layer in a thread joined to that desktop and drive it with windows the test creates: min-size refusers, frameless, tool windows, layered, different DPI, windows that resize themselves. Assert `SetWindowPos` round trips, invisible-border compensation, minimise/restore, release-all. | Never |
| L1b Hook delivery on the hidden desktop | Whether `SetWinEventHook` fires for windows on a non-input desktop (hooks are per-desktop, **imagined**; verify first) | Never |
| L2 Shadow mode on the real desktop | Observe-only: the engine computes where it *would* put windows from the live WinEvent stream and logs the difference to real rects. Nothing moves | Never (a log) |
| L3 Supervised live | Alex's own windows, announced beforehand ("windows will rearrange"), watchdog armed, one hotkey ready | Yes, by his say-so |
| Existing evidence tools | `hidden_evidence.py` renders the actual pages in headless Edge; `test_kdesk.py` surrogate HWND tests | Never |

Cannot be tested on a hidden desktop: AppBars interacting with Explorer (shared work area), real GPU/Chromium drag jitter on a visible monitor, game gating, multi-monitor. Those belong to L2/L3.

---

## 7. Appendix: other tools, for ideas only

| Tool | Licence | Idea worth taking |
|---|---|---|
| GlazeWM | GPL-3.0 (**ran**) | `window_effects` per focused/other window: border colour, corner style (square/rounded/small_rounded), transparency, hide title bar (Win11 only); `gaps.inner_gap/outer_gap` with `scale_with_dpi`; `hide_method` cloak/hide/place_in_corner; `binding_modes` (a resize mode). **Read** `sample-config.yaml` |
| Zebar | GPL-3.0 | HTML widgets as packs, `privileges.shellCommands` allow-list, presets with anchor/offset/monitor |
| yasb | MIT (**read**, with the upstream da-rth/yasb MIT notice kept) | adaptive "islands" bar, theme gallery with one-click install, window-level taskbar widget |
| Whim | MIT (**ran**) | C#; I did not read it |
| PowerToys / FancyZones | MIT (**ran**) | zone snapping; also a reference for Windows quirks |
| komorebi-application-specific-configuration | MIT (**read**) | the 227-app rule list |
| windows-icons | MIT (**ran**) | UWP/exe/hwnd icon extraction |
| tinted-theming schemes/shell | MIT (**ran**) | 230+ palettes |

---

## 8. Open questions

For Alex (each blocks a design choice):

1. **"When something new is opened it should minimize other things. Things can tile freely, or fill the space if it's full already."** Do you mean (i) always minimise everything else (focus mode), or (ii) place the new window in free space and minimise the least-recently-used only when it cannot fit, with "fill the space" meaning the new window takes whatever is left? I built on (ii).
2. **What is a pin?** An immovable window everything else arranges around, or also visible on every workspace, or also always on top? And do you want workspaces/spaces at all, or one flat desktop?
3. **Everything or opt-in?** Manage every ordinary window from the start, or only windows you adopt (the earlier prototype used one key per window)? A browser with many windows is the hard case.
4. **Windows taskbar:** the current desktop already sets Explorer to auto-hide and hides it, with a recovery lease. You said you would toggle Windows settings yourself. Keep the guard, or will you hide it in Settings and let Agora only draw?
5. **Sharing posture:** will Agora be handed to neighbours with window management included? If yes, option (a) is out, and no komorebi code may be reused.

For Claude (coordinator):

6. Where does the engine live? A pure Python module beside `kd_window.py` (my suggestion), with the world holding only intent, since lens-driven layout measured 25 to 2150 ms.
7. Who owns the shared token vocabulary (section 2.3)? It touches `lens.js`, the component painter and host CSS, so it needs the agora and painter owners.
8. Should the komorebi adapter exist at all, given the grey area for communities? I would build it last, if at all.
9. Is a Cal Poly account likely to be added as a Work-or-school account on this PC? It would flip komorebi's MDM check.

---

## 9. What I did not verify

Alex's photos; komorebi running (nothing installed or run); `win32-display-data` honouring AppBars; Zebar's framework (Tauri or other); base24 slot meanings, mustache template format and `SHQueryUserNotificationState` details (recalled, not fetched); the WorkerW technique on build 26200; transparent WebView2 dock; hook delivery on a hidden desktop; live drag smoothness on Chromium windows; any timing for a pure engine; Whim's source. The survey in 6.3 is a single reading of one moment with Agora's bars running.
