# Presentation and operators

Presentation should make ordinary changes cheap while leaving new forms and
interactions programmable. Its useful scope includes **style**, **composition**
and **arrangement**, not just window coordinates.

## Retained intent and supported surfaces

A rule can select current or future surfaces and contribute properties or a
behavior. Scope can use identities, tags, collections, regions or supported
capabilities. Selection does not grant authority. Incomplete selection and
unsupported targets should be visible rather than presented as full success.

A surface or adapter can expose stable parts such as title, body, toolbar or
composer. Different renderers can support different properties. Outer window
geometry can be editable even when an application's interior is opaque. Subjects,
appearances, nested coordinate systems and local stacking contexts need not be
flattened into one global board.

## Composition and computation

Themes, regional rules, local exceptions and gestures may all contribute to a
result. Make their resolution understandable: per-property precedence, a layout
container, an ordered transform or a domain-specific solver are possible choices.
One contributor, one engine and one global ordering are not universal requirements.
Reading/slot order is different from front-to-back stacking.

An operator names an arrangement action, targets and parameters. Idempotence is
useful for tidying operations such as alignment; translation, incremental rotation,
animation and simulation have other useful meanings. Movement priorities can
favor stable slots, reading order, compactness or visual balance. There is no
universal minimum-displacement metric or convergence promise.

Even idempotent nearest snaps to multiples of 5 and 7 can cycle between 5 and 7
despite sharing fixed points. Budget exhaustion, detected cycles and demonstrated
infeasibility are different outcomes. Engines can choose scheduling and fallback
policies; attachment order and suspending the newest rule are only possible defaults.

## Applying, maintaining and interacting

Apply once can commit literal placements. A maintained rule can instead derive
geometry, or commit placements under an explicit policy. Retain understandable
intent separately from disposable measurements and caches. A closed view may
pause evaluation or use a supported headless path; it does not invent live sizes.

Dragging may reorder, offset, detach one appearance, move a container or invoke
a domain action. A local exception need not suspend an entire layout. Pure
arrangement leaves semantic facts alone; a declared drop can change a task stage,
collection or relationship through the normal authorized action.

Undo should target the relevant intent or accepted operation and respect later
edits. Reversing coordinates alone does not undo a rule that recreates them.
Gesture previews can be local and cancel without durable writes. Animation is an
optional explanation, subject to focus, motion preferences and responsiveness.

## Measurement and truthful feedback

Requested, minimum, preferred and effective sizes are different. Text wrapping
can require measurement under a proposed width followed by bounded remeasurement.
Measurements describe their viewport, constraints, units and freshness. A view
may scroll, reflow, retain a usable result or explain an unsatisfied request.

Preview should make the expected change observable before commitment. Compare
rendered results with declared intent, including exact sizing where meaningful.
Shared implementation code helps but cannot make different inputs, mobile CSS
or manual overrides equivalent. Precision, units and cross-host agreement are
contract-specific; integer arithmetic or the same binary does not replace tests.

Selection, focus, scrolling, drafts and text continuity are part of presentation.
An inspector should explain contributing rules, overrides, affected targets,
unavailable inputs and recovery. Important intent changes belong in native
history; every frame, measurement or animation step need not become an event.

## Extensibility and execution

Use installed schemas for discovery, parameters, examples and inspection. A small
preview/apply/maintain/edit/remove interface is helpful without being the only
possible vocabulary. New renderers, operators and evaluators remain packages.
Pure signatures and property tests are not sandboxes or universal proofs. Actual
execution boundaries, output validation and resource limits support those claims.
Trusted bounded interpretation and isolated authored execution may use different
runtimes; no permanent language or host/guest topology is prescribed here.

## Evidence from the small slice

The September 9 isolated experiment added style rules, grid/align/snap, chat
composition, scope, local placement exceptions, inspection and rule undo to the
existing shell. Two prepared view kinds—notes and reference cards—shared rules.
JEFF then authored circle support beyond the catalog.

Across nine matched requests, the prototype used 740.6 summed seconds versus
1498.1, and 3 source saves versus 12. These are one-trajectory observations with
preparation excluded, not a statistical benchmark. Both variants ultimately met
the scenario requests. Circle overlaps were disclosed rather than hidden.

The prototype's composer minimum-height bug was repaired by JEFF during the run.
Subsequent human tests found selection loss, a registry-field mismatch and a
geometry-only preview. The separate review build repaired those; real input
verified zero-write visible style preview, Keep/Undo, selection and draft
continuity. This evidence supports a small reusable contract, not a finished
visual language. See [[Implementation Status]] and [[Native Development]].
