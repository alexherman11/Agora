# Atlas ports

Atlas owns `surfaces/atlas`, view `atlas.surface` and canvas/drop host `atlas.host` (`dropRole: card-host`). Shared Studio cards can move into this host through `card.move {id,x,y,drop}`. Studio confirmed static `card.face` and `card.tools` addresses and a 190 by 120 card box with center `(x+95,y+60)`.

Atlas owns `connections` records with `fromId` and `toId` card references. Commands are `atlas.connect {id,fromId,toId}` and `atlas.disconnect {id}`. Both endpoints must exist, differ, and currently have host `atlas.host`. Connections must be removed before either endpoint leaves Atlas or is deleted. Line endpoints derive from card positions in every scene render and gesture preview.

After first-render evaluation, Atlas child boxes use `["frame","width"]` and `["frame","height"]` so Toolkit's effective mosaic size governs the title, palette, canvas, footer, and resize grip. The canvas can scroll when a small window cannot fit all 190 by 120 cards. Atlas's card metadata is a compact overlaid `NODE` badge, leaving Studio's edit row usable.

The Atlas surface has role `surface`; its title and resize grips have roles `surface-grip` and `resize-grip` for Toolkit's generic window gestures. Atlas contributes global `role:surface` borderRadius `6px` at priority 10, deliberately conflicting with Studio's `20px` at the same priority. Toolkit's higher priority preference can override both.
