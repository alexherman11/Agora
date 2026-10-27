# Themes

Builder draft, 26 October 2026, for Claude's review and Alex's gate. One theme is one palette and one shape language
for every window, bar, dock and widget on the desktop. A theme is a small piece of data that anyone can make, export,
share on the board and try on, and every theme is checked before it can be worn, so a neighbour's theme can restyle your
desktop but can never run anything on it.

Everything is in `research/kernel-lab/theme/`. The words are a module (`theme.*`). Evidence is in `theme/evidence/`.

Labels in this file: **ran** (executed; the number is what was printed), **read** (read in a source), **imagined**
(design, not tried).

## The format

A theme is a JSON object, `format: "agora-theme"`, `version: 1`. It is closed: any key not listed here is refused.

```
meta      name author licence variant(light|dark|auto) tags from description
palette   base00..base0F (base16), optional base10..base17 (base24); #rrggbb
roles     bg surface raised bar ink ink-muted border select accent accent-ink ok warn danger info focus scrim
          each a slot name (base0D), a #rrggbb colour, or another role; missing roles take defaults
type      ui mono display (font names only), size 11..22, scale 1.0..1.6
shape     radius(none|small|medium|large) border 0..4 gap_inner 0..32 gap_outer 0..48 bar_height 24..64 dock_size 32..96
surface   bar_opacity 0.2..1  window_opacity 0.5..1  shadow(none|soft|deep)  blur(none|soft)
motion    fast medium slow (ms)  ease  reduce
windows   focused unfocused pinned attention (border colours)  corner(square|small|round)
icons     style(native|plate|mono)  plate
wallpaper kind: none | gradient (1-4 layers) | svg (inline, cleaned) | image (inline png/jpeg/webp)  fit dim(0..0.8)
```

Palette slots follow tinted-theming base16/base24, so any scheme published for terminals and editors is a theme here
(`theme.import`). Roles are what the desktop reads; the palette is what people pick. `resolve()` (theme/model.py) fills
the defaults, derives base10-17 when a base16 scheme gives only sixteen, chooses `accent-ink` for contrast, and decides
light or dark from the background. The compiler (theme/compile.py) turns the result into three things:

| output | what it is | who reads it |
| --- | --- | --- |
| `theme.css` | `--ag-*` custom properties (see below) | every page and window |
| `theme.json` | the css, the legacy painter tokens, palette, roles, hash, source, `until` | `theme-live.js`, the widget host |
| `theme-native.json` | gaps, border width, corner, radius, state colours, bar and dock size, bar opacity | the window manager, the shell |

The variable names are the contract the window manager and shell builders consume: `--ag-bg --ag-surface --ag-raised
--ag-bar --ag-ink --ag-ink-muted --ag-ink-faint --ag-border --ag-select --ag-accent --ag-accent-ink --ag-accent-soft
--ag-ok --ag-warn --ag-danger --ag-info (and -soft of each) --ag-focus --ag-scrim --ag-hover --ag-active
--ag-base00..17 --ag-font-ui/mono/display --ag-text --ag-scale --ag-radius-s/m/l/pill --ag-border-w --ag-gap-inner
--ag-gap-outer --ag-bar-height --ag-dock-size --ag-bar-opacity --ag-window-opacity --ag-bar-bg --ag-window-bg
--ag-shadow --ag-backdrop --ag-dur-fast/med/slow --ag-ease --ag-win-focused/unfocused/pinned/attention --ag-icon-plate
--ag-icon-filter --ag-wallpaper(-size/-repeat/-dim) --ag-variant`. Note `--ag-border` is a colour, `--ag-border-w` a width.

## Safety: what is refused, and how it says so

The check (theme/model.py `validate`) refuses, naming the place and the reason, and reports every reason at once:

- any key that is not part of the format (a raw `css` key, a `script` key);
- a font that is not a plain family name: no `<`, `;`, `{`, `(`, quotes, `url(` or `@import`; fonts are names, never files;
- any colour that is not `#rrggbb`, a slot or a role (so `url(...)`, `expression(...)` and named colours are refused);
- numbers outside their range;
- an SVG wallpaper with script, `style`, `foreignObject`, `image`, `a`, `animate`, `text`, entities or a doctype, any
  attribute outside an allow-list, any `href` or `url()` that is not `#local`, more than 4000 elements, nesting deeper than
  16, or more than 128 KiB (`svgsafe.py`);
- a raster wallpaper that is not an inline `data:image/png|jpeg|webp;base64` whose bytes are that picture, or is over
  150 KB decoded;
- a whole theme text over 300 KB.

The check runs at three doors, so there is no side way in: the `theme.import`/`theme.edit`/`theme.make` words, the
kernel's own `make`/`set` (a `validate_write` hook for `kind=theme`, painter/handles.py), and a kit being taken
(kernel/kits.py). A theme that fails the check later is never worn: the gallery skips it and says how many it skipped.
The wallpaper is served from its own route with `default-src 'none'; sandbox`, so even a picture cannot run.

**ran** (scratch world): `type.ui` with a script, `url(` in a font, a colour that is `url(javascript:...)`, a raw `css`
key, a 320 KB SVG, an SVG with script, an SVG that fetches an address, and a 200 KB PNG were each refused with a reason
naming the path and left the log unchanged; the same bad font inside a kit was refused whole; a theme written straight
with `make kind=theme` was refused by the kernel hook (proof output at the end of this file).

Why the sizes are small (**ran**): the kernel splits a word's line with `shlex.split`, which is quadratic in the line
length, and a theme travels as a line. A 100 KB picture took 1.5 s end to end, 200 KB took 6 s, 400 KB took 25 s, and a 1.6
MB line kept the kernel busy for minutes. So pictures are limited to 150 KB and SVG to 128 KiB. This is a kernel limit, not
a theme one (Rough spots, below).

## The words

A module, `theme.*`, not kernel words. The kernel gained no theme verb. Reasons: the words need no private access (they read
and write ordinary things: `kind=theme`, `theme-settings`, `theme-choice`, and nothing else); a module gives process
isolation for the parsers of untrusted text (YAML, SVG); it can be turned off (`off theme`) and the look stays; and the
dotted namespace is already how window.*, media.* and system.* work. What could not be a module is *serving* the look to a
page: that is the door's job, so the door gained four read-only routes and the module and the door share one pure function
(`service.pick`) so they cannot disagree.

```
theme.list [mine=yes]            the themes you may see, each as a card (palette, shape, look, who wears it)
theme.get <theme>                one theme in full, with derived values and contrast
theme.current                    which theme you wear and why: place | me | trial (and until, for a trial)
theme.use <theme>                the place's theme (a steward)           theme.use place for=me   follow the place
theme.use <theme> for=me         just yours; wins over the place for you
theme.try <theme> [seconds=30]   wear it for a while; it goes back by itself
theme.keep / theme.revert        keep the trial / go back now
theme.import yaml=|json=|text=   a base16/base24 scheme or an agora-theme.json, checked, as a theme of yours
theme.export <theme> [format=agora|yaml|css]   a downloadable file (a row with filename and text); yaml, or base16, is the
                                 sixteen colours for any other program
theme.make <theme> [name=]       your copy to edit
theme.edit <theme> path=value..  change a theme you made (palette.base0D=#c4a8ff shape.radius=large wallpaper=preset:dusk)
theme.preview <theme> path=value..  what an edit would look like; writes nothing
theme.options [theme=]           the safe fonts, shapes and wallpaper presets an editor offers
theme.native / theme.css         the native sheet / the css for you
theme.starters                   (steward) add the starter themes that are missing
```

Things: `kind=theme` (name, title, `text` = the canonical JSON; made by anyone with `theme.import`/`theme.make`, or by the
module for the starters), `kind=theme-settings` (`active`; only a setting made by the steward or by the module acting for
the steward counts as the place's theme, so a forged one is ignored), and `kind=theme-choice` (one per person: `theme`,
`trial`, `trial_until`; private, `sees=person:<them>`, so nobody sees what someone else wears). A trial that runs out is
not undone by writing: `service.pick` compares the trial's end with the kernel clock, so it reverts even if the module is
off; the module only announces `theme.changed` (delivered, not recorded) so pages refresh at once.

Scopes, in order of power for one person: a trial, their own choice, the place's theme, the built-in Seabright Day.
`theme.use` writes one thing and `undo` removes it, so one act, one undo.

## Delivery: how every surface wears it

The door serves, for the signed-in person (read-only, ETag, 304):
`/theme.css  /theme.json  /theme-native.json  /theme-wallpaper?h=<digest>` (and the same under `/desk/` in the desktop).

- **Host pages** (bar, taskbar, frame, help, lines, tasks, thing, widget) link `theme.css` for first paint and load
  `theme-live.js`. It asks `theme.json` again whenever the kernel says `theme.changed` or `undo`, when the page returns to
  the front, when a trial ends, and every 15 s as a backstop. A new css replaces the old in one `<style>`: no reload. It
  dispatches `ag-theme` on `window`.
- **kd.css / bars.css** are written entirely in `--ag-*` variables with today's colours as fallbacks, so a page that loses
  `theme.css` still reads (this is what keeps an older running desktop looking as it did).
- **Widgets** (the guarded iframe): the host builds the iframe's `<style id="ag-theme">` from the theme, sends a new one by
  `postMessage` on `ag-theme`, and `agora.theme()` returns the painter's legacy tokens (paper, card, ink, muted, accent,
  the colour names) *as roles* plus `css`, `roles`, `palette`, `variant`. `pin_style=yes` keeps the old per-widget
  style tokens. `widgets/common.js` reads `var(--ag-*)` with the token as fallback, so older widgets repaint live too.
- **Component painter**: the painter's tokens are the theme's roles. A lens that writes colours of its own (the board's
  `nb-soft`, `--board-colour-N`) wrote them for the light look, so `painter/themed.js` re-wears each: neutrals ride the
  theme's ink-to-surface ramp, a coloured one keeps its hue family and takes the theme's colour for that family. In Seabright
  Day this is close to the identity; a lens that wants its colours exactly sets the token `pin-colours`. The painter remounts
  its parts on `ag-theme` (components that took colours at mount stay right).
- **Native**: `<world>/modules/theme/theme-native.json` is rewritten (debounced) on every change for the theme the *place*
  wears, and `theme-native.json` is served per person. The window manager and shell read it for gaps, border width, corner,
  state colours, bar and dock sizes.

## Sharing

- **File**: `theme.export` gives one `agora-theme.json` (a wallpaper SVG or picture is inside it); `format=base16` gives
  the sixteen colours for any other program. `theme.import` takes either back. Importing is a *new* thing of yours, so a
  neighbour can never overwrite your theme by sharing one.
- **Kit**: a theme travels in a kit like any definition (`FIELDS["theme"]` = name, title, text). The text is opaque to the
  kit's reference scan (a theme says `base0D` and `#ff0000`, which read like ids), validated as a theme on export and take.
- **Board**: the Appearance app's Share posts to a channel with a preview picture and the theme file attached, using the
  board's own words (`board.post`, `upload`, `attach`); neighbours Import the file. If the place has no board it says so and
  offers the file.
- Licence: imported schemes keep their licence (base16 schemes are MIT); the starters are CC-BY-4.0 except where noted in
  each theme's `meta`.

## The starters

1. **Seabright Day**: today's light look, warm off-white, green accent `#638779`. White text on that accent is 3.98:1 as
   it is today; it is kept so the place does not change (the other four meet 4.5:1).
2. **Dusk**: violet gradient, lavender accent, translucent bar, large corners, gaps.
3. **Night Metal**: near-black, pale-blue borders, square, monospace, tight gaps.
4. **Ink Landscape**: cream paper, ink-brown text, teal and rust, thin square borders, monospace, and a drawn SVG wallpaper of
   hatched ink mountains (about 19 KB, made by `wallpapers.py`).
5. **Catppuccin Mocha**: made by `theme.import` from the published base16 values (`starters/catppuccin-mocha.yaml`, MIT).

No downloads were used; the inspiration images were only looked at.

## The Appearance app

`theme/components/appearance.js` (a reviewed painter component) with `theme/appearance.lens` (arrangement only: every
button is a word the viewer already has) and `theme/install.py` (`install(door)` is scratch-safe; `--live` is for the
coordinator). Three tabs:

- **Gallery**: live preview cards, each a miniature desktop (bar, three windows, dock) painted *in that theme* by setting
  the same variables on the card. Try 30 s, Use just for me, Use for everyone (stewards only), Make my own from this,
  Export. While a trial runs the top strip shows a countdown with Keep and Go back.
- **Make your own**: a live preview that follows each change (the preview word writes nothing; the real theme is saved on
  release and `undo` works), sixteen named colour pickers, accent choice, safe-list fonts, text size, corner radius, gaps,
  border, bar height, dock size, bar and window opacity, shadow, glass, wallpaper presets and dim.
- **Import and share**: paste a scheme or choose a file, export as agora-theme.json or base16, and Share to the board.

## Not done, and what could change

- **Only the desktop is themed.** The web door's own pages (`/web`, sign-in) have the routes but no theme link; the Seabright
  public site is untouched.
- **Old lens styles** (`desk-shell/lens.js`, which I did not edit): an old `style` note still paints its own colours. The
  smallest general fix is a lens style token that opts in to `--ag-*`; I did not emit generated style notes.
- **Installed widgets keep the JS they were installed with.** The painter, `common.js` and the components are stored in the
  world, so a live desktop needs the install re-run (and `component` review) to get the new painter. The coordinator rolls
  this out; I did not.
- **The window manager and shell** consume `theme-native.json` and the `--ag-*` variables; I have not seen them do so.
- **Pasted files over 60 KB** cannot go through a widget line (the bridge limit is 64000 characters); a picture-heavy theme
  moves by file, kit or the board's attachment, not the paste box.
- **One steward**: the module's idea of "the steward" is the person it works for.
- **Blur** is approximated (`backdrop-filter` where the page has it); native acrylic is the window manager's.
- **Contrast is advice, not a gate.** Ink on surface below 4.5:1 is warned about (`theme.get` and the import receipt show the
  ratio), not refused: a neighbour may want a low-contrast look. The accent's text colour is chosen for contrast by the
  compiler, but a theme that names its own `accent-ink` is taken as written (Seabright Day's is 3.98:1, as today).

What would change my mind: if the window manager needs to react to a theme *before* a page loads, the native sheet should
become a kernel read rather than a file; if neighbours want themes that restyle one app only, scopes need a per-lens
layer (the painter already has `personal-style`); if the 150 KB picture limit pinches, the right fix is a faster line
parser in the kernel, not a bigger limit.

## Rough spots (source edits outside theme/)

Each source edit and the world-level word that was missing (also noted for the board, f747):

- `kernel/door.py`: four read-only routes (`/theme.css`, `/theme.json`, `/theme-native.json`, `/theme-wallpaper`). Missing:
  a way for a module to *serve* a read-only per-person document through the door.
- `kernel/kits.py`: `FIELDS["theme"]`, `OPAQUE` fields. Missing: a way for a kind to say "this field is data, not words
  that name things", so theme JSON is not rewritten as references.
- `painter/handles.py`: a `kind=theme` validation in `validate_write`. Missing: a way for a module to register a check on
  the things it owns that the kernel runs inside `make` and `set`.
- `painter/painter.js`, `painter/themed.js` (new), `painter/primitives.js`, `painter/install.py`, `widgets/common.js`,
  `components/card.js`: the painter reads the theme as roles and re-wears a lens's own colours. Missing: a lens-level
  word for "wear the theme" versus "pin my colours" (today it is the token `pin-colours`).
- `window-lab/kernel-desktop/kdesk.py` (module spec, `THEME_GRANTS`, `/desk/theme*` routes), `widgets.py` (`theme()`),
  `pages/*.html` (theme link and `theme-live.js`), `pages/kd.css`, `pages/bars.css`, `pages/widget-host.js`,
  `pages/theme-live.js` (new), `pages/icons/palette.svg` (Lucide, ISC), `widget_browser.py` (the test firewall now allows
  the theme routes). Missing: host chrome that reads variables instead of literals.
- **Kernel, not changed:** `kernel/lines.py` uses `shlex.split`, quadratic in the line length. A 400 KB line took 25 s. Any
  word with a long argument pays it, so a neighbour can stall the door by sending one. The word that is missing is a line
  length limit at the door and a linear tokenizer.
- **Kernel, not changed:** a place's kit carries every module word's help text, and the kit's reference scan reads any
  `ab12`-shaped token in it as a thing id. `base16` in the theme words' help broke `kit <place>` ("a definition refers to
  data outside the kit"), which `test_widgets.py::test_kits_copy_code_without_activation_or_grants` caught. The theme
  words now say "base 16" and `format=yaml`. The word that is missing: help text that is not scanned as a reference.
- **Kernel, not changed:** a module is not told about an `undo` of its own act (`hear:undo` is granted and nothing
  arrives), so the theme module also reads the two small kinds that decide what anyone wears every 3 s and rewrites the
  native sheet when they change. The word that is missing: a happening for `undo`, delivered like any other write.

## Evidence

Run: `C:/Projects/Agora4/.venv/Scripts/python.exe research/kernel-lab/theme/proof.py` (about 6 minutes; hidden Chromium, scratch
kernels only; it builds the board's own two-week world, adds the theme module and the Appearance app to it, and makes a
second scratch desktop for the file transfer). Nothing touches 127.0.0.1:8810.

**ran**, last line as printed: `THEME PROOF {"checks": 57, "failed": [], "live_desktop_touched": false, "shots": 40}`.
Unit tests: `pytest research/kernel-lab/tests/test_theme.py` (22). With them the whole kernel-lab suite printed
`102 passed, 30 subtests passed in 105.16s`; the desktop's `test_kdesk test_widgets test_shell_icons test_widget_overlay
test_stream_windows test_pixel_guy test_window_activation test_sysread test_widget_native` printed
`59 passed, 39 warnings, 17 subtests passed in 66.81s`; the board's `test_polish test_contracts test_ui_transport` 18 passed;
the board's hidden Chromium acceptance printed `BOARD UI: 104/104 checks passed`; the regression runner's `kits`, `widgets`
(23 of 23), `pixel-guy`, `painter-contract`, `painter-purpose`, `painter-isolation`, `taskboard`, `taskboard-v2` exited 0.
`painter` (painter/proof.py) fails at "Five app components arrange the board": the lens in `apps/taskboard` gained a
`text-block` summary part in commit 04c39dce3, so the plan now counts six components; that is not from this work.

Screenshots (all in `theme/evidence/`, each looked at):

- `sheet-<starter>.png` for seabright-day, dusk, night-metal, ink-landscape, catppuccin-mocha: the board, the Appearance
  app, a widget made with the old vocabulary, the taskbar and a host page, together.
- `<starter>-board.png`, `-appearance.png`, `-widget.png`, `-taskbar.png`, `-help.png`: the same, full size.
- `delivery-dusk-*.png` and `delivery-undone-*.png`: the one-act switch and the one-undo return.
- `appearance-trial.png`, `-import.png`, `-editor.png`, `-share.png`: the app in use.

What the screenshots showed and was fixed: the miniature desktop's bar and dock were sized with an invalid `calc`; the
widget host's receipt strip was a fixed pale green under every theme; the trial countdown read the page's clock, not the
kernel's; a share into the board stopped after the post because the `attach` fence had not seen the new things; and the
native sheet did not follow an `undo`.
