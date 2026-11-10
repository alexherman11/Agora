# Agora desktop: the contracts between the builders

*Draft by Claude (coordinator), 26 Oct 2026, from Alex's ask and [RESEARCH.md](RESEARCH.md). Three builders work in parallel against these contracts. A builder that needs to change one says so in its report instead of drifting. Alex can revise anything here.*

Alex's ask, in his words: "a cleaner top and bottom bar. Things should be clickable and useful. I dont want clutter. ... Windows should not tile over each other. When something new is opened it should minimize other things. Things can tile freely, or fill the space if its full already. Things can be pinned to the screen, resized from any corner, etc. I want dragging a window around to move other windows out of the way. ... The task bar icons should be in color, and represent what the things are. They should be centered on the bottom. ... the biggest consideration is that it should support people being able to share their own custom theming, and for it to work across the system."

## Decisions taken (Claude, under Alex's authority to commission and iterate)

1. **Agora's own window manager (RESEARCH option b/c1).**
   - Komorebi doesn't do Alex's behaviours: no free placement, no minimise-on-full, and a drag only swaps on release.
   - Its licence forbids distributing it, or work based on it, to the community.
   - So we study komorebi and copy none of its code. We reuse only MIT material (the application rules list, the icon approach), with notices kept.
2. **"Minimise others" means RESEARCH option (ii).** A new window goes into free space at its preferred size. If nothing fits, the least recently used unpinned windows minimise until it fits. The setting `when_full` also offers `fill` (the new window takes all the free space) and `focus` (everything else minimises).
3. **A pin is a window that stays where it is,** and everything else arranges around it. It is not "always on top": nothing overlaps, ever. Showing a pin on every space can come later.
4. **Every ordinary window is managed, after shadow mode.** The rollout runs: observe and log only → Alex says go → live. There is a "leave this app alone" rule per app, seeded from the MIT application rules. Games and full-screen apps are never touched.
5. **No change to Windows settings without Alex.**
   - The existing taskbar guard stays as it is, since it's reversible and already in use.
   - The wallpaper is drawn by Agora's own desktop layer, not by changing the system wallpaper.
   - No URL protocol registration.
6. **One theme reaches everything.** A theme is a world thing. It compiles to one set of CSS variables, used by every painter, bar, widget and Agora window, and to one small native sheet for window gaps and borders.

## 1. The theme (owner: theme builder)

**The thing:** `kind=theme`, a closed schema, so kits can carry it.

| Section | Contents | Notes |
|---|---|---|
| meta | name, author, licence (default CC-BY-4.0), variant `light\|dark`, tags, `from` (for example `base16:catppuccin-mocha`) | |
| palette | `base00`…`base0F` required; `base10`…`base17` optional, derived when absent | Exactly tinted-theming's base16/base24 slots, so any published scheme imports unchanged |
| roles | overrides only; defaults below | |
| type | `ui`, `mono`, `display` font stacks (names only, never files or URLs), `size` (base px), `scale` | |
| shape | `radius` (none\|small\|medium\|large), `border` (px), `gap_inner`, `gap_outer` (px), `bar_height`, `dock_size` | |
| surface | `bar_opacity`, `window_opacity` (0–1), `shadow` (none\|soft\|deep), `blur` (none\|soft: approximated) | |
| motion | `fast`, `medium`, `slow` (ms), `ease`, `reduce` | |
| windows | border role per state: `focused`, `unfocused`, `pinned`, `attention`; `corner` (square\|round\|small) | |
| icons | `style` (native\|plate\|mono), `plate` role | Native colour by default |
| wallpaper | an asset reference, `gradient` spec, or `none`; `fit`; `dim` | Assets travel with the theme |

**Default roles:**

| Role | Default | Role | Default |
|---|---|---|---|
| bg | base00 | accent | base0D |
| surface | base00 | accent-ink | base00 (or base07 when accent is light) |
| raised | base01 | ok | base0B |
| bar | base01 | warn | base09 |
| ink | base05 | danger | base08 |
| ink-muted | base04 | info | base0C |
| border | base02 | focus | base0D |
| select | base02 | scrim | base00 at 60% |

**CSS variables, the one vocabulary for every web surface:**
- palette: `--ag-base00` … `--ag-base17`;
- roles: `--ag-<role>`;
- type: `--ag-font-ui`, `--ag-font-mono`, `--ag-font-display`, `--ag-text` (base size), `--ag-scale`;
- shape: `--ag-radius-s`, `--ag-radius-m`, `--ag-radius-l`, `--ag-radius-pill`, `--ag-border`, `--ag-gap-inner`, `--ag-gap-outer`, `--ag-bar-height`, `--ag-dock-size`;
- surface: `--ag-bar-opacity`, `--ag-window-opacity`, `--ag-shadow`;
- motion: `--ag-dur-fast`, `--ag-dur-med`, `--ag-dur-slow`, `--ag-ease`.

The painter's legacy tokens map onto roles: paper→surface, card→raised, ink→ink, muted→ink-muted, accent→accent, red/orange/blue/sage/… → nearest palette slot. Existing components keep working and pick up the theme.

**Which theme applies:**
- the place default, `theme-settings.active`;
- a person's own choice ("just for me"), which wins for them;
- a lens may still pin its own style, which the shared theme can show as a deliberate exception.

**Delivery:**
- `theme.css` is served by the host for every Agora page and window.
- The painter, widget bridge, bars and host chrome all read it.
- A change publishes the happening `theme.changed`, and every surface repaints without a reload.
- `theme-native.json` is the native sheet: `{gap_inner, gap_outer, border_width, corner, colors:{focused, unfocused, pinned, attention}, bar_height, dock_size}`. The window manager reads it.

**Words:**
- `theme.list`, `theme.use <theme> [for=me]`, `theme.try <theme>` (applies for 30 s, then reverts unless kept), `theme.keep`;
- `theme.import base16=<yaml text or file>`, `theme.export <theme>`;
- `theme.make from=<theme>`, which copies a theme to edit.

Themes are data only: no JS, no remote URLs, values checked by the painter's existing validators.

## 2. The window manager (owner: WM builder)

**Process:** a module named `wm`, its own process, using the module protocol (`agora/SHAPE.md` §17).
- **Layout engine:** pure and deterministic, with no Win32.
- **Win32 host:** a WinEvent hook, `SetWindowPos` with frame compensation, real minimise, DWM border colour and corners on windows it places.
- **Watchdog:** a separate process that owns the panic hotkey and the lease file, and restores every saved placement if the manager dies or the hotkey is pressed.

**The world holds intent only:** pins, per-app rules, settings and mode. Geometry lives in the module and its readings, never in the log.

**Words (all with help; acts undoable where they change world intent):**
- `wm.windows` (see): one row per managed or visible window. Fields:
  - `key` (stable for the window's life), `app` (program display name), `exe`, `icon` (reference), `agora` (a window thing id when it's an Agora window);
  - `state` normal|minimised|pinned, `focused`, `rect`, `space`, `managed`, `why` (why it's unmanaged, if it is).

  **No window titles in rows or the log;** the dock asks the host for a live title only when hovering.
- `wm.focus <key>`, `wm.minimise <key>`, `wm.restore <key>`, `wm.close <key>` (asks the window politely to close; never kills a process).
- `wm.pin <key>` / `wm.unpin <key>`: a world fact about the app and its placement.
- `wm.arrange` (re-solve now), `wm.mode live|shadow|off`, `wm.leave-alone <app>` / `wm.manage <app>`.
- ~~Happening `wm.changed` (throttled to ≤10/s) with the changed keys, for the dock and top bar.~~ Removed 26 Oct (Claude, from Alex: "visual state should not live in the world"); the shell polls `wm.windows`.
- Settings thing `wm-settings`: `when_full` minimise-oldest|fill|focus, `manage` all|adopted, `drag` ghost|live, and `never` (a list of apps).
  - *Added 26 Oct (Claude builder; WM.md "Feel"), all optional, validated, defaults shown:* `dwell_ms` 350
    (0–2000), `snap_px` 16 (0–64, at 100 % scale), `deadzone_px` 10 (0–64), `motion_ms` 250 (0–1000), `pin_min` 0.5
    (0.2–1.0), `edges` shared|free.
  - These are preferences, not screen state. A bad value is refused as a whole (the last good settings stay) and
    is said once on stderr.
- *26 Oct:* the `wm.windows` row fields are unchanged. A new `why` value is `owned dialog or popup` (managed
  false). A maximised window keeps `managed` true and `state` normal, but floats outside the layout until it is
  un-maximised.

**Behaviours** (*26 Oct: pins are no longer immovable; see the next paragraph and WM.md "Feel"*): no overlap; free placement in the best free rectangle; minimise least recently used when full; pins immovable. Dragging pushes neighbours aside along the axis of least overlap, cascading, shrinking to minimum size, then minimising the least recently used. A ghost preview comes first; live movement only if it measures smooth. A resize from any corner pushes in the same way. Gaps and borders come from `theme-native.json`.

*Revised 26 Oct (Claude builder, from Alex: "a bit of resistance... like moving apps around on the homescreen"):*
- **Drags.** A drag passes over neighbours; a neighbour gives way only after the drag rests on it (`dwell_ms`).
  It swaps into the dragged window's old slot, or slides aside, or shrinks its own facing side (never under
  60 %).
- **Release** is exactly what the ghosts showed. The dragged window lands on its outline: the nearest free spot,
  snapped at the gap.
- **Resizes.** A resize stops at a neighbour, then shrinks it after a dwell. Windows snapped edge to edge share
  that edge (`edges=shared`).
- **Pins** stay on screen: they are never minimised or moved off by the WM. A big new window may narrow a pin
  to `pin_min` of its pinned width, and the pin grows back when space frees.
- **Squeezing.** Nothing is squeezed under 60 %. Past that, the covered window is minimised.

**Safety:**
- **Shadow mode is the default on first run.** The manager computes and logs and moves nothing.
- **Games and full-screen apps:** `gaming_gate.py` plus `SHQueryUserNotificationState`. While gated, the manager does nothing.
- **Never touched:** elevated or unmovable windows, which become fixed obstacles.
- **Placements are saved** with the process identity before the first move, and restored on off.
- **Off:** the panic hotkey Ctrl+Alt+Backspace, one click in the top bar, and `wm.mode off`, all ending in the same release-all.

## 3. The desktop shell (owner: shell builder)

Top bar, centred dock and desktop background, all as painter components and lenses reading only `--ag-*` variables. They talk to the manager only through the words above. Agora's existing bar windows (`kd_window.py` AppBars) are the hosts.

**Top bar:** slim and translucent, and every element is a button with a small popover.
- Left: the Agora mark (opens the launcher, Lines), space chips (only if there's more than one), and the focused app's icon and name (window menu: pin, minimise, close).
- Centre: time and date (opens a calendar and notifications popover).
- Right:
  - the notifications count;
  - media, as one control;
  - one status cluster for network, volume and battery, opening quick settings;
  - JEFF's presence dot;
  - off (two presses).

Optional readings (CPU, memory) are off by default.

**Dock:** a centred floating pill with colour icons.
- Order: the Agora mark, pinned apps, running apps, Agora's own windows, then a separator and the overview.
- Markers: a dot under running apps, a stronger mark on the focused one, dimmed when minimised.
- Actions: click to focus, or minimise if it's already in front; middle-click for a new window; right-click for the app's windows and pin/unpin; hover for a live thumbnail.
- Contents: no clock, readings or tray.

**Icons:** real colour icons at 64 px or more with alpha (exe, window icon, UWP package logo). Agora apps get their own colour icons. The fallback is a theme plate with a letter.

**Desktop background:** Agora's own window under all apps, showing the theme's wallpaper or gradient. Spike the WorkerW method on a hidden desktop first. If that doesn't work, draw a bottom-most Agora window and say what's lost.
