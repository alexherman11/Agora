# Component painter reach

Builder draft, 24 October 2026. **Imagined:** purposes below drive the primitives;
they are not claims that an application is implemented. Written before replacing
the stopped run's painter. **Read:** the widget board, lens board v2 and SHAPE 17.

The core owns layout, content, input/focus, overlays, motion, bindings and a 2D
surface. Components compose those pieces and theme tokens. Applications arrange
components, bind facts and name words. A calendar is not a scheduling service; a
map is not a tile provider; a code surface is not an IDE. Keep those distinctions
visible in discovery.

| Purpose | Core primitives | Catalogue pieces | Coverage / missing layer |
| --- | --- | --- | --- |
| Seabright feed | stack, text, image, press, scroll | list, avatar, badge | Compose; moderation words belong to the world |
| Seabright map | canvas, layers, press, focus | map, tooltip | Local points only; geographic tiles/routing missing |
| Neighbour chat | stack, text, type, live rows | list, input, avatar | Compose; delivery/read receipts need facts |
| Rooms | grid, press, live rows | list, badge | Compose; realtime audio/video service missing |
| Polls and votes | stack, select, press | choice, progress | Compose over vote words |
| Sign-in page | stack, type, focus | input, button, feedback | Form only; trusted authentication stays outside components |
| Events calendar | grid, text, press | calendar, popover | Month dates; recurrence and time zones missing |
| Task board | grid, stack, drag, live rows | board, lane, card, flag, menu | First app under proof |
| Writing room / document editor | split, rich text, type, focus | editor, toolbar | Plain/Markdown editing; collaborative rich text missing |
| Worker dashboard | grid, live rows, text | table, progress, badge | Compose; worker control remains granted words |
| JEFF bar | row, text, press | avatar, badge, input | Compose inside existing bar surface |
| Spotify-style player exposing verbs | row, image, media, press | player, progress | Local/inline assets; playback backend is separate |
| Tiling window manager | split, drag, keyboard | split-pane, tree | Layout only; native moves remain window words |
| Browser chrome | row, type, press, focus | toolbar, input, tabs | Chrome only; privileged browsing is not granted |
| Pixel guy | canvas, layers, motion | pixel-surface | Drawn surface; original native guy stays separate |
| Pixel editor | canvas, press, type, grid | pixel-surface, choice | Compose; export through a word |
| System bar | row, live rows, press | badge, progress, menu | Compose in a bar slot |
| Tray widget | row, press, overlay | icon, popover | Compose; OS provider separate |
| Charts | canvas, text, focus | chart, tooltip | Local series; no statistical engine |
| Dashboard | grid, responsive, live rows | chart, table, progress | Compose |
| Phone layout | stack, responsive, drawer | list, tabs, drawer | Compose; responsive browser surface |
| Settings page | grid, type, select, focus | input, choice, switch | Compose; writes are words |
| Command palette | overlay, type, keyboard | palette, list | Compose; searchable supplied commands |
| File browser | split, scroll, press | tree, table, menu | Compose; filesystem provider separate |
| Photo gallery | wrap, image, overlay | gallery, dialog | Inline/local assets; no cloud photo import |
| Timeline | row, scroll, text | timeline | Ordered events; zoom/calendar scheduling missing |
| Kanban | grid, stack, drag | board, lane, card | Task board proves this use |
| Spreadsheet-like table | grid, type, select | table, input | Readable rows; formulas/range editing missing |
| Form builder | stack, drag, type | input, choice, button | Compose forms; visual form-authoring app missing |
| Game HUD | layers, canvas, motion | progress, badge | Draw only; no game engine |
| Notifications | stack, overlay, motion | toast, badge | Compose; durable delivery requires facts |
| Recipe / cooking timer | stack, image, type | list, progress | Compose; durable timer provider separate |
| Community directory | grid, text, image | list, avatar, input | Compose; privacy is door visibility |
| Search results | scroll, text, keyboard | virtual-list, input | Windowed rows; search word supplied separately |
| Email triage | split, text, select | table, editor, menu | Compose; mail adapter separate |
| Meeting agenda | stack, drag, text | list, timeline, progress | Compose |
| Council vote tally | grid, live rows | chart, table, badge | Compose over privacy-filtered tally |
| Reading / annotation room | split, rich text, select | editor, list, popover | Selection available; shared Comment integration missing |
| Diff review | split, code, scroll | code, badge | Code display; semantic diff engine missing |
| Terminal / logs | scroll, code, virtual rows | virtual-list, code | Display only; arbitrary shell execution not supplied |
| Audio waveform editor | canvas, media, drag | pixel-surface, player | Surface only; waveform decoding/editing missing |
| Video call grid | grid, media, responsive | gallery, avatar | Layout only; WebRTC and device grants missing |
| Node graph editor | canvas, layers, drag | pixel-surface, popover | Surface only; graph routing/selection missing |
| Budget planner | table, type, chart | table, input, chart | No finance connector or formula engine |
| Habit tracker | grid, press, live rows | calendar, progress | Compose; history remains world facts |
| Accessible kiosk | stack, focus, keyboard | button, choice, dialog | Defaults supplied; screen-reader/native validation still required |
| Inventory / lending shelf | grid, press, live rows | table, badge, dialog | Compose over claim/return words |
| Music sequencer | grid, canvas, press | pixel-surface, player | Surface only; precise audio scheduling missing |
| 3D CAD editor | layers, canvas, drag | none | Not covered: no 3D scene, geometry or GPU renderer |
| Collaborative desktop publishing | rich text, grid, drag | editor, gallery | Not covered: pagination, typography engine and concurrent rich text |

## Chosen deep primitives

`layout` (stack/row/grid/wrap/split/layers/scroll, responsive CSS), `content`
(text, safe Markdown, code, icon, image/avatar, media), `input` (text, multiline,
choice, toggle, press), `overlay` (menu/popover/tooltip/dialog/toast/drawer),
`motion` (transition, spring, enter/exit), `canvas` (2D/pixels), `collection`
(ordered children and windowed long rows), and `focus` (labels, tab order,
keyboard navigation, focus return). Fact selection and streaming invalidation
are core services, never a component's private database.

The first catalogue prioritises small composable pieces. Collection names do
not imply full domain services. Its cards, examples, live gallery and guide must
say exactly which layer exists. The fresh discovery trial includes 3D CAD and
collaborative publishing to test honest refusal as well as successful discovery.

## Evidence status

This document is the map. Coverage statements become **ran** only in the proof
and frozen trial reports beside it. No live installation follows merely from
an entry in this table.
