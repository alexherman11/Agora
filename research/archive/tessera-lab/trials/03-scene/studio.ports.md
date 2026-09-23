# Studio ports for the scene trial

Agreed directly with Atlas and Toolkit builders:

- `studio.host` is a canvas with `dropRole:"card-host"` inside `studio.surface`. The studio surface is seeded with `dock:"left"` so Toolkit can place it in mosaic mode while retaining free coordinates.
- Shared cards are rendered once by `card.list` → `card.portal` → `card.shell`. The portal targets each `cards.host`; the shell has role `shared-card`, a 190 × 120 box, and top-left at `cards.x/y`. Its center is `x+95,y+60` for Atlas connectors.
- `card.face` and `card.tools` are static extension addresses under the shared shell. Atlas and Toolkit may add children or styles. `card.grip` has role `card-grip` for the Studio drag gesture.
- `card.move {id,x,y,drop}` commits free movement in the current host; drops on `studio.host`, `atlas.host`, or `console.host` change `cards.host` and reset local x/y to 24,24. Atlas protects linked cards from deletion or leaving its host until disconnected.
- `card.drag` requests `dropRole:"card-host"` so the gesture resolves the actual hovered host. Its preview is local; `card.move` is the sole commit.
- `studio.resize` is a `resize-grip` under `studio.surface`, allowing Toolkit's generic resize gesture to apply. Studio host height derives from effective `frame.height` after mosaic and resize styles, not the seed size.
- `card.create {id,title,body}` creates a card in the Studio; `card.edit {id,title,body}` and `card.delete {id}` work on shared cards regardless of host.
- Studio independently contributes `role:surface` `borderRadius:20px` at priority 10. Atlas contributes a competing radius at the same priority; Toolkit may override both at priority 30 based on user preference.
