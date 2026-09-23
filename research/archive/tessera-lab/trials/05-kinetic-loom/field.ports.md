# Field ports for Kinetic Loom

Field owns `fields/main` with `x`, `y` and signed `strength`: positive attracts, negative repels, zero disables. Actions are `field.place {x,y}` and `field.setStrength {value}`. The handle is view `field.handle` with row identity `main`, under Motion's fixed logical `motion.world` canvas. Its grip has role `force-grip`; the handle has role `force-handle`.

Motion confirmed `motion.body` is a positioned surface occurrence keyed by each body ID, with center equal to the body's logical x/y and extension ports `motion.body.face` and `motion.body.tools`. Field contributes `field.forceStep` to `sim.step` as `add` deltas on `bodies.vx/vy`; Motion contributes friction `add` deltas to those same cells. Both use the pre-step snapshot. Field's measured viewport lines address `field.handle/main` and `motion.body/bodyId`, so the lines follow movement and world rearrangement without feeding geometry into state.

After the moving-body drag conflict observed in the browser, Motion is introducing counter offsets and public `motion.poseX {id}` / `motion.poseY {id}` derivations. Field's force, near-body query, and body proximity badge now read those pose ports. This keeps physical force and visible glyph positions aligned during drag previews and concurrent simulation steps; the geometry lines continue using measured rendered occurrences.

Instrument confirmed `instrument.controls` as the tuner parent and owns positioning of `motion.world`. Field deliberately contributes `role:body` borderRadius `8px` at priority 10; Motion contributes `50%` at priority 10, and Instrument offers a priority 30 override and an off mode exposing the conflict. These ports were negotiated directly before implementation reads.
