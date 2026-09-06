# Executable component validation — September 5, 2026

Implementation evidence for [[Executable Components]]. This follows the earlier
[[implementation-validation-2026-09-05]] declarative-lens work. The scope changed
because Alex explicitly requires JEFF to invent abilities during use.

## Result

The runtime supports authored UI behavior, scoped object reads/writes, owned
persistent state, disposable interaction candidates, pinned activation, and actions
discoverable without restarting JEFF. A real Sonnet 4.5 conversation authored
dragging, revised the same component with an alphabetize button and usage counter,
and invoked its new action. No drag or alphabetize implementation was supplied in
the runtime or JEFF prompt. Hand-authored examples exist only in test fixtures.

This is a working local experimental slice. It does not establish reliable
arbitrary authoring, a model advantage over conventional tools, hardened native
code isolation, or distributed execution. The authoring friction is substantial
enough to affect the next product experiment.

## Automated checks

- `uv run pytest`: **114 passed**, one upstream Starlette/AnyIO deprecation warning.
- `uv run ruff check .`: passed.
- `uv run ruff format --check .`: 75 files already formatted.
- `node --check shell/app.js` and `node --check shell/components.js`: passed.
- `git diff --check`: passed. No duplicate note basenames under docs/research.

The component tests cover transient dragging versus durable release, content
preservation, event provenance, replay/reopen equality, owned state, protected
facet refusal, atomic refusal of mixed valid/invalid effects, candidate isolation,
caller separation, stale fingerprints and display revisions, pinned source,
interpreter termination/recovery, unavailable ambient
capabilities, fresh global state, and new action tools in the same Agent turn.
Additional cases assert that pointer motion cannot persist even when state is
permitted, nested node expectations check requested fields, and a live render
failure leaves state and log unchanged.

## Real-provider trials

Full tool arguments, errors, replies, and final trees are retained in
`executable-component-validation.json`. All tasks used synthetic notes in separate
worlds; no personal objects were given to the trials. The fixture UI world is
explicitly labeled as hand-authored, separate from live-model evidence.

| Trial | Outcome | What it exposed |
|---|---|---|
| Configured `anthropic/claude-haiku-4.5`, initial attempt | Neither request activated a component within the temporary 18-step trial limit | Malformed bindings/permissions, encoded objects instead of objects, and unclear style refusals |
| Haiku retry, nested schemas, 12-step limit | Neither request activated | Invalid JavaScript, stale edits, and `ctx.local || defaults` failing because empty objects are truthy |
| `anthropic/claude-sonnet-4.5`, 12-step limit | First request reached passing drag tests but stopped before activation; follow-up revised and activated | Existing turn budget was too small; node-style assertions needed recursive matching |
| Fresh Sonnet 4.5, final protocol and 24-step limit | All three requests completed | Corrected binding/handler/style mistakes before admission; follow-up corrected an object lookup; action invocation succeeded |

The final three prompts were:

1. “JEFF can you make it so I can click and drag the notes around?”
2. “Add a button that alphabetizes the notes into a row, remember how many times I
   used it, and give yourself an action to do the same. Revise the same component.”
3. “Use your new alphabetize action now.”

The final component remained the same entity, ending at definition revision 8.
Its first activation implemented dragging. The revision added sorting and state;
the third turn called the public `invoke_component` gateway for its newly declared
`alphabetize` action. Dynamic tool advertisement is additionally exercised by a
deterministic same-turn Agent test. Do not report the real trial as having chosen
the `extension_alphabetize` tool: it chose the generic invocation tool.

The final trial started with notes in reverse alphabetical order. The new action
placed Garden notes, Reading list, and Weekend ideas at x=24, 264, and 504, y=100,
and persisted count=1. Provider replies sometimes overstate polish; actual calls,
state, and browser behavior are the evidence. Earlier errors were retained, not
discarded from the report.

The personal `.env` model choice was not changed. The separate demonstration
server uses Sonnet 4.5 for subsequent chat. These trials support that model's
ability to complete the example with correction; they do not show that the
configured Haiku model now reliably authors executable components.

## Browser and restart checks

The first Sonnet-authored component, revision 4, was exercised through the real
shell at localhost:8788:

- Dragged Garden notes from browser coordinates (24,170) to (364,370); reload
  preserved the location. The world advanced by one recorded decision.
- Clicked Alphabetize: note positions changed and the persistent count became 1.
- Opened the latest draft in a disposable candidate and clicked Alphabetize.
  Candidate count became 2; the live revision stayed 17. Closing returned to count 1.
- Stop prevented a subsequent button click. Default desk and Restore previous
  display recovered the admitted component with its saved count.

The fresh successful conversation was copied to the separate persistent demo
world `worlds/executable-demo-20260905` through a stable log copy. Its store was
rebuilt and compared with the source. The demo server was restarted on that world:

- Revision 8 and count=1 rendered on the newly started server.
- Dragged Garden notes from (24,170) to (339,355); reload preserved the location.
- Alphabetize restored the sorted row and persisted count=2.
- Rebuild after these interactions matched the current store exactly.

These direct interactions require no provider request. Definitions and state
live in the world, independently of the authoring conversation. The local demo is
at <http://127.0.0.1:8788/> while its server runs. The personal app at port 8787
was restarted with updated server code; HTML, CSS, app.js, and components.js all
returned 200 with their correct media types on both ports.

## What deserves the next experiment

The runtime passes the requested capability test, but the authoring experience
still needs work. Measure success rate, latency, cost, and human corrections
across several unrelated requests and model choices. Give JEFF compact, precise
runtime observations; avoid compensating with a large private agent framework.

The example cards show names, not full note contents, and reference the explicitly
bound notes. Adding a new note does not automatically expand the program's read
scope; JEFF must revise the manifest or a future query-binding contract must make
that behavior explicit. The generated interface also needs independent usability
and accessibility checks; passing self-authored tests is insufficient.

A component owns one state schema, and restoration checks compatibility with
current state. Migration, multiple simultaneous components, a durable registry of
installed actions, chat-panel composition, external effects, packages, shared
rooms, and device distribution remain desired capabilities. Invocation limits
and a separate interpreter process do not replace an OS sandbox for hostile
native-engine exploits. Local server round-trips are acceptable for this proof,
but need measurement before remote and mobile use.
