# Trial 5: Kinetic Loom

A new application, not a reskin of the window/card workspace. Three authors build
an interactive live particle instrument. The shared root and state vocabulary are
the entire scaffold. No cards, host registry, or prebuilt visual layout is inherited.

Base state: bodies(label,x,y,vx,vy,radius,color), simulation/main(running=false,
steps=0,width=1000,height=640). vx/vy are COUNTERS so separate force contributions
can add deltas. x/y are registers. `sim.step {dt:0.05}` is shared: authors contribute
independent reactions evaluated at the same pre-step snapshot, then joined. Base
only increments steps. Body positions are in a fixed logical 1000 by 640 world;
authors negotiate how the world is shown and moved. No hidden shell physics.

New general runtime primitive, provided by coordinator: `pulse` declaration
`{kind:"pulse",id:"transport.clock",everyMs:50,when:EXPR,action:"sim.step",args:{dt:0.05}}`.
Exactly one LOCAL SERVER owns pulses, regardless of browser count. No catch-up
storms: if late, execute one fixed step and schedule the next. Minimum 50 ms.
Pulses sharing a scheduled instant join into one atomic command batch. A refused
pulse stays refused and is paused with a diagnostic until its definition or guard
changes. No callbacks, no host code, no external clock access in expressions.
State and pulse receipts are persisted. Closing a tab does not pause a running
simulation; the authored transport must expose Pause. Simulation starts paused.

New general expression arithmetic: abs, sqrt, sin, cos, pow are pure operators.
Optional runtime module switch in the diagnostic inspector allows withdrawing an
author's BEHAVIOR AND VIEWS while keeping their field declarations and saved data.
This is an explicit author-layer switch, not deleting source or silently rewriting it.
All active module arrival orders and all contributor subsets will be exercised.

Assignments, direct peer negotiation required:

* Motion (notes_builder): seed 12-20 varied bodies; add `motion.step` reaction to
  sim.step which integrates x/y with toroidal bounds. Add one force reaction on the
  SAME vx/vy cells as Field author (e.g. drag/friction). Create shared body glyph
  template and body.drag command/gesture. Publish stable occurrence/extension ports.
  Own motion.tessera.json and motion.cases.json only.
* Field (tasks_builder): independently authored tunable force field(s) that react
  to sim.step, affecting SAME vx/vy as Motion without overwriting its contribution.
  Author a draggable attractor/repulsor with controls and live vector relationships
  using measured geometry. Add per-body visual contributions at Motion's ports.
  Own field.tessera.json and field.cases.json only.
* Instrument (library_builder): design the whole visual experience as a distinctive
  laboratory/instrument, own stage style and adaptive arrangement. Start/Pause/Step,
  pulse declaration, live derived statistics, floating movable inspector/controls.
  Add one alternative appearance mode that changes spatial presentation. Competing
  role:body visual claims must be exposed/resolvable as an authored user choice.
  Own instrument.tessera.json and instrument.cases.json only.

All three may contribute children/styles to peers' public addresses. Use compact
JSON formatting: one declaration per paragraph/line, expressions on a few readable
lines. Do not generate thousands of pretty-printed single-token lines. No JS/HTML/
CSS source, no feature code or edits to coordinator runtime, no edits to peers.
First modules frozen before testing. Repairs made only by their author. Agree
cross-module IDs directly through messages and write own ports notes. Use existing
scene language where possible; report truly missing general semantics.

Acceptance: continuous dynamics combine forces, a body and force handle are
draggable during motion, pause really stops mutations, additional browser clients
do not multiply steps, different appearance changes live objects, module subsets
remain usable/diagnosed, withdrawal and restoration preserve object identity and
state, competing styles preserve both proposals, concurrent disjoint edits proceed.
Performance is measured and reported at 20 and larger body counts; no benchmark
promise is baked into acceptance. Browser observations can fail authored cases.
