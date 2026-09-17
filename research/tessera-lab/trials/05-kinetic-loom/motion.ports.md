# Motion ports for Kinetic Loom

Agreed directly with Field and Instrument authors:

- `motion.world` is a direct child of `scene`, fixed logical 1000 × 640 canvas. Instrument positions and styles its outer frame without scaling logical coordinates. Body state `bodies.x/y` is the glyph center in world coordinates.
- `motion.bodies` lists every body. `motion.body` is the stable surface occurrence addressed by its body record ID, with role `body`; its box uses `(poseX-radius,poseY-radius,2radius,2radius)`. `motion.body.face` and `motion.body.tools` are open extension ports. `motion.body.face` carries role `body-grip` for drag.
- `motion.step` joins `sim.step` to integrate x/y from the same pre-step velocity snapshot with toroidal bounds. `motion.friction` adds `-0.12 * dt * oldVelocity` to each vx/vy counter. Field's `field.forceStep` also adds to those exact counters; no reaction assumes a handler order.
- `bodies.dragX/dragY` are additive counters independent of simulator-owned x/y registers. `motion.poseX/Y {id}` derive the visible/physical center as toroidal `(base + drag offset)`. Field uses these exact pose ports for forces and proximity; vectors follow the measured body occurrence.
- `body.drag {id,dx,dy}` adds user displacement to those counters. Legacy `{id,x,y}` requests convert an absolute target to a delta against current pose. `motion.bodyDrag` previews and commits displacement, so a running pulse can advance base position without making the drag a stale x/y write.
- Motion independently claims `role:body` borderRadius `50%` at priority 10; Field independently claims `8px` there. Instrument can override the conflict via a user preference at priority 30 and expose it when disabled.
