# Motion ports for Kinetic Loom

Agreed directly with Field and Instrument authors:

- `motion.world` is a direct child of `scene`, fixed logical 1000 × 640 canvas. Instrument positions and styles its outer frame without scaling logical coordinates. Body state `bodies.x/y` is the glyph center in world coordinates.
- `motion.bodies` lists every body. `motion.body` is the stable surface occurrence addressed by its body record ID, with role `body`; its box uses `(poseX-radius,poseY-radius,2radius,2radius)`. `motion.body.face` and `motion.body.tools` are open extension ports. `motion.body.face` carries role `body-grip` for drag.
- `motion.step` joins `sim.step` to integrate x/y from the same pre-step velocity snapshot with toroidal bounds. `motion.friction` adds `-0.12 * dt * oldVelocity` to each vx/vy counter. Field's `field.forceStep` also adds to those exact counters; no reaction assumes a handler order.
- `bodies.dragX/dragY` are additive counters independent of simulator-owned x/y registers. `motion.poseX/Y {id}` derive the visible/physical center as toroidal `(base + drag offset)`. Field uses these exact pose ports for forces and proximity; vectors follow the measured body occurrence.
- `body.drag {id,dx,dy}` adds user displacement to those counters. Legacy `{id,x,y}` requests convert an absolute target to a delta against current pose. `motion.bodyDrag` previews and commits displacement, so a running pulse can advance base position without making the drag a stale x/y write.
- Motion independently claims `role:body` borderRadius `50%` at priority 10; Field independently claims `8px` there. Instrument can override the conflict via a user preference at priority 30 and expose it when disabled.

## Live population and scenario ports

- Motion owns `selection.bodyId` and seeds `selection/main` with empty selection. `motion.selectedBody {}` returns the selected body or null. `body.select {id}` accepts an existing body ID or empty string to clear selection.
- `body.create {id,label,x,y,vx,vy,radius,color}` creates a body; `body.duplicate {id,newId}` copies current visible pose and physical properties with a 34px offset. Both are automatically included by `motion.bodies.all` and the motion/force reactions.
- `body.delete {id}` removes a body and clears selection if it was selected. Deleting a seed is a normal runtime tombstone; module reload must preserve it. `body.kick {id,dvx,dvy}` adds velocity deltas to the currently selected body while the pulse continues.
- Instrument owns `scenario.capture {id,name}` and `scenario.restore {id}` with `scenarios.bodies` as an array of full body records, including dragX/dragY. Motion's `motion.selectionOnRestore` reaction clears selection when the captured body population lacks the selected ID. Field owns its force-source snapshot in the same scenario ID.
- Motion contributes editable population controls under Instrument's `instrument.controls`; Field may read `selection/main.bodyId` or `motion.selectedBody` for diagnostics without hardcoded body IDs.
