# Scene toolkit ports

- Toolkit owns `settings/scene` with `theme` (`night` or `dawn`), `mode` (`free` or `mosaic`), `borderOverride` (`round`, `square`, or `off`), and `focusSeq` (counter).
- Toolkit seeds `surfaces/console` and owns `console.surface`, its title grip `console.grip` (role `surface-grip`), resize grip `console.resizeGrip` (role `resize-grip`), and `console.host` canvas (`dropRole:card-host`). Studio cards may be dropped into `console.host`.
- Toolkit provides `surface.move {id,x,y}`, `surface.resize {id,width,height}`, `surface.focus {id}`, and `surface.dock {id,dock}`. Gestures target `role:surface` with the agreed grips; each action writes only the target surface fields plus focus sequence where needed.
- `scene.theme {theme}`, `scene.mode {mode}`, and `scene.borderOverride {value}` control dynamic style claims. A priority30 `role:surface` borderRadius rule is active while override is round or square. It is absent when override is off, revealing Studio's priority10 20px and Atlas's priority10 6px conflict.
- `mosaic` mode uses each surface's `dock` slot: left, right, or bottom. Studio agreed to seed `dock:left`; Atlas was asked to seed `dock:right`; console seeds `dock:bottom`. Free mode uses authored surface boxes untouched. Moving a window sets its dock to free.
- Studio owns `card.face` and `card.tools`; Atlas owns `atlas.host`; both use role `surface` and title/resize grip roles. Toolkit will add small nonbehavioral children to the shared card addresses after initial freeze if desired.
