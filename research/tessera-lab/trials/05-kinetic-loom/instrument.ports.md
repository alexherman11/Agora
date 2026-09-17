# Instrument ports

- Motion owns `motion.world` as a direct child of `scene`, fixed logical 1000 × 640. Instrument positions and skins that view without scaling it, so body drag x/y remain logical pixels. Motion owns `motion.body` occurrence and `motion.body.face` / `motion.body.tools` child ports.
- Instrument owns `instrument.controls`, a stack inside the inspector; Field and Motion may contribute tuner widgets there. The inspector is a movable surface with `instrument.grip` as its drag handle.
- Instrument owns `instrument.start`, `instrument.pause`, `instrument.mode`, `instrument.bodyOverride`, `instrument.moveInspector` actions. Shared `sim.step {dt:0.05}` stays in base; an authored pulse calls it every 50 ms only while `simulation/main.running` is true. Start and Pause are explicit state transitions.
- `instrument.mode` switches laboratory and observatory scene arrangements. World remains 1000 × 640 in both. Below 1600px viewport width, the stage scrolls and the inspector is placed below the world, preserving access to peer controls.
- Motion claims `role:body` borderRadius `50%` at priority10; Field agreed to claim `8px` at priority10. Instrument's priority30 `borderRadius` override may be `glow`, `ink`, or `off`; off exposes the authored equal-priority conflict, and either on value resolves it.
- Instrument's body aura is also priority30 only while an override is active. In `off`, Motion's priority8 body shadow applies, avoiding an unrelated permanent conflict.
- Derived `instrument.count`, `instrument.meanSpeed`, and `instrument.motionEnergy` read all live bodies and support status displays; no motion logic lives in Instrument.
