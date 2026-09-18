# Toolkit Trial 4 ports

- Toolkit seeds `hosts/console.host` with label `Control console`, using Studio's `hosts.label` field. The existing `console.host` remains a `card-host` drop surface. Studio confirmed the host registry and owns `studio.host` plus `reading.host`; Atlas owns `atlas.host`.
- `settings/scene` now defaults to `mode:overview` and `focusId:studio`. Modes: `free`, `overview`, `focused`. `scene.focusSurface {id}` focuses any existing surface; `scene.mode {mode}` switches modes.
- `scene.rank {id}` derives a stable lexical ordinal from all current `surfaces` IDs. `scene.columns`, `scene.rows`, `scene.tileWidth`, `scene.tileHeight`, `scene.overviewX {id}`, `scene.overviewY {id}`, `scene.focusRank {id}`, `scene.mainWidth`, and `scene.mainHeight` drive generic responsive geometry. No peer-specific slot or dock names are used.
- Overview uses two columns at viewport widths at least 1300px, one below. Tiles retain at least 480px height and the scene scrolls. Focused mode shows the selected surface large with every other surface in a rail at widths at least 1000px, or a scrollable stack below it on narrower viewports.
- A fixed scene toolbar provides persistent surface selection, focus, overview/free switches, theme, and conflict override. Console retains detailed controls and remains a card host.
- Existing `surface.move`, `surface.resize`, `surface.focus`, `surface.dock` actions and window gestures remain. In overview/focused modes, geometry is derived from surfaces and viewport; preferred free coordinates remain in records and return when mode becomes free.
- Studio and Atlas intentionally claim different `role:surface` borderRadius at priority10. Toolkit priority30 override can be switched off to expose the equal-priority conflict, then restored.
