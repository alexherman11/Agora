# Proposal: an Agora application layer JEFF can develop during use

Status: proposed for Alex's review, not implemented. September 5, 2026.
This extends the approved executable-component direction. It does not change the
current runtime or grant the running JEFF additional authority yet.

## Recommendation

Give JEFF development authority over the local Agora world and make the whole
application layer editable through that world: source, UI, tools, skills, data
definitions, dependencies and installed versions. Keep a small host responsible
for recording facts, running programs, authentication, delegation and recovery.

Use executable application packages stored as objects, with automatic build,
candidate execution and live replacement. This combines Agora-native source
editing with the useful part of hot reload. JEFF does not need a checkout,
terminal or permission to patch Python to invent ordinary application behavior.

Do not make the current render-tree whitelist the universal UI instruction set.
Do not merely mirror repository files as objects and let JEFF edit them: that is
still platform self-modification, with the same replay and upgrade problems.

## Evidence from the running application

Alex asked JEFF: “Can you make it so that scrolling with my mouse zooms in and
out on the notes?” JEFF read the current definitions and correctly replied that
mouse-wheel events are unsupported, offering zoom buttons instead.

The blocker is implemented in both `kernel/component_tree.py` and
`shell/components.js`: a closed event list omits wheel. It is not an OAuth,
model-intelligence or ordinary permission problem. Related structural limits:

- A short list of tags and CSS properties determines all possible rendering.
- Every gesture is processed through a server round trip and a fresh JS context.
- Bindings enumerate individual objects and only three readable facet types.
- Component effects permit placement and name/text attachment, plus owned state.
- Only the currently displayed component contributes discoverable actions.
- The conversation, composer and surrounding shell are repository HTML/JS.
- Skills and JEFF's working procedure are repository prompt text.
- New application facet definitions remain a documented ambition rather than a
  general implemented world operation.

Loosening permissions cannot supply missing execution facilities. Adding wheel
to the list would fix this one request while retaining the recurring problem.

## What “development authority” means

An operator-selected local development profile delegates to JEFF the ability to
create, discover, edit, test, install, replace and remove application objects,
register tools and skills, define application data, change every normal UI
surface, and delegate these world capabilities to installed programs. Within
this profile, ordinary iterations do not require individual permission prompts.

The profile belongs to the operator; a module cannot activate it by claiming to
be trusted. It can initially be broad across the local world. That avoids building
fine-grained multi-user policy now while retaining one place to introduce it later.
Every call still has an authenticated caller, executing package/version and
delegation context. A manifest describes a request, not the authority itself.

Development authority does not mean direct SQLite writes, editable past events,
access to OAuth tokens, or operating-system root. Those are different powers and
are unnecessary for the requested interface freedom. Kernel recording, validation,
version checks, attribution and a recovery path remain structural invariants.

## Application packages as ordinary objects

Introduce a general program/package record with a versioned runtime contract.
Optional parts include UI entry points, headless actions, skills, application
schemas, assets, tests, migrations and dependency references. Do not require a
large publication manifest for every local experiment.

Packages have named source files, stable entity IDs and immutable source revisions.
JEFF gets package read, search and patch operations with revision preconditions.
File names are paths inside a package, never arbitrary host filesystem paths.
Build output is an immutable artifact with source/dependency hashes. Dependencies
are pinned package revisions; reusable library imports can later include explicitly
resolved external packages. Do not execute arbitrary dependency install scripts.

Keep current `core.lens` and version-1 `core.component` objects readable and runnable.
Add the more general package format rather than silently changing their semantics.
Do not wrap every internal UI function in a separate object; package reusable or
independently replaceable units, with ordinary modules inside each package.

## A browser execution surface with native interaction

Run authored UI JavaScript in a separate browser document, with its own DOM and
CSS, rather than interpreting a tiny tree into the host DOM. Browser-supported
wheel, pointer, keyboard, focus and touch events, canvas/SVG and animation become
ordinary authoring facilities. Features no longer require new event cases in
Python and the trusted shell.

Use a sandboxed document and an explicit message channel to a trusted bridge.
The document does not receive the host session token or direct parent DOM access.
The bridge authenticates the mounted package revision and effective authority;
it does not trust actor or privilege fields supplied by the document. Control
external resource loading separately from DOM expressiveness. Native browser
behavior is broad but still varies by device and browser.

Keep gesture state in the renderer. For the current zoom request, JEFF handles
wheel deltas locally, maintains a camera scale/offset and keeps the world point
under the pointer fixed. Camera/view preferences are appearance or participant
state, not changes to the notes. If persistence is desired, coalesce a completed
gesture into a state write. Do not append an event or call the server per frame.

An iframe sandbox is an access boundary, not a guarantee of separate CPU/process
isolation. Preview should run separately from the current application; background
workers need explicit termination. Recovery must work independently of a broken
authored renderer. Avoid claiming hostile-code isolation that has not been tested.

Browser platform references:
[sandboxed frames](https://html.spec.whatwg.org/multipage/iframe-embed-object.html#attr-iframe-sandbox),
[wheel input](https://developer.mozilla.org/en-US/docs/Web/API/Element/wheel_event),
[message channels](https://developer.mozilla.org/en-US/docs/Web/API/MessageChannel).

## A general world API and installed capability registry

Provide shared program operations for read/query/subscribe, world mutations,
owned state and installed action invocation. In development mode, programs can
use the broad delegated world scope, including creating objects and updating
programs. Queries replace manually binding a fixed list of note IDs: a lens can
follow all notes in a scene, including notes created after installation.

Introduce a versioned application-data definition path, consistent with the
vernacular facets already described in Objects and Facets §3.7. Start with JSON
schemas, a generic projection and supported merge behavior. Defining an application
type cannot redefine event storage or claim constitutional authority. Custom
projectors are pure programs whose dependencies and revisions are explicit.

New tools are package entry points with names, descriptions and argument/result
schemas. Installing a package registers them independently of what is visible.
Both JEFF and UI programs discover and invoke the same installed actions. An
organizer tool keeps working after its lens is closed. Dependencies permit tools
to reuse tools without copying large source strings.

Do not add a Python verb per authored action. A generic installed-action invocation
enters the host gateway; application code composes existing world primitives.
Mutation batches and schema changes still commit through `verbs` and events.
Effects record the executed package/version and actual resulting facts. Replay
must never execute either old or new package code.

Separate transactional world changes from asynchronous jobs and external I/O.
An external operation needs an explicit job/result lifecycle; rollback of a
program is not rollback of an email, network request or file export. Initial
delivery can offer UI and headless world actions. Timers, subscriptions and
background workers extend the same package/registry model with cancellation,
loop prevention and bounded resources.

## Make the shell and JEFF's working material native

Bootstrap the current desk and conversation as an installed shell package, with
replaceable regions or imported UI modules. JEFF can then move or redesign the
chat panel, composer, navigation, inspectors, previews and application layout.
An arbitrary number of independently installed tools does not imply an arbitrary
number of separate panes; composition is itself authored application behavior.

Expose conversation records, messages, run status, tool receipts and submit/stop
operations through an Agora service contract. Conversation content is durable
world data; OAuth secrets and provider transport state remain host-owned. Reloading
the chat should preserve its draft, selection, visible messages and active run.
Rebuilding the world must not resend a user message to the model.

Skills become versioned procedure objects with examples, references and optional
associated actions. JEFF can create, revise and install them under development
delegation, then discover them during the same session. The harness distinguishes
installed procedures from arbitrary text in a note; installation is an explicit
recorded operation. Skills guide behavior and do not grant authority or silently
change the user's instructions. Credential handling and host authentication are
outside JEFF's editable working material.

Keep a minimal independent recovery surface for stopping runs and selecting a
previous installed shell. It need not permanently occupy the right side of the
screen. The visible chat interface can be fully authored. Recovery should also
be reachable from a separate route or host control when the main UI is broken.

## Development workflow and live replacement

The normal loop is inspect → patch package → build → exercise candidate → inspect
errors/view/state → install the tested artifact → continue. JEFF needs console
errors, stack traces, current UI structure, screenshots and actual browser input
tests as Agora development tools. These tools target Agora surfaces and candidates,
not an unrestricted browser or the host checkout.

Browser tests must exercise real event delivery. Merely calling a handler with a
fabricated event would not have caught the missing wheel listener. Use fixed
behavioral acceptance cases as well as JEFF-authored tests; self-authored passing
tests alone do not establish that a requested interface works.

Keep draft revisions separate from installed revisions. Promote source, build,
dependencies and compatible state migration together under an expected-current
installation check. Healthy installed UI continues while a candidate fails.
Routine changing note contents should not invalidate every test receipt: receipts
pin program/runtime/dependencies, while activation checks current input compatibility
and explicit migration preconditions. Do not remove meaningful stale-write checks.

Live replacement preserves stable objects, camera, selection, drafts and compatible
state. In-flight actions finish or cancel under their original pinned version;
new calls resolve the new installation. Code restoration does not automatically
undo world data. State migrations and compensating data changes must be explicit.

Replace hidden fixed development ceilings with visible run budgets and cooperative
continuation. The current 24-call limit is small for building an application. Let
JEFF continue an authorized development run without requiring the person to keep
resubmitting it, while preserving Stop and per-invocation resource limits. This
proposal does not imply infinite spend, runaway jobs or independent future runs.

## Concrete implementation areas

| Area | Proposed work |
|---|---|
| `kernel/facets.py`, vocabulary and verb gateway | Add package, installation, skill, data-definition and conversation contracts; derive all development tools from them. |
| Component/package runtime | Add UI bundle and headless entry points, generic brokered world access, pinned dependencies and explicit state migrations. Keep version-1 execution compatible. |
| `kernel/component_data.py` | Replace active-display-only discovery with installed-package discovery for the new runtime. |
| `shell/index.html`, `app.js`, `components.js`, `server.py` | Introduce authored browser surfaces, bridge, native conversation UI and independent recovery; preserve existing views during migration. |
| `jeff/context.py`, `component_guide.py`, provider adapters | Teach package development and installed-skill discovery, expose development feedback, support longer cancellable runs; retain provider authentication outside the world. |
| Tests | Add real input delivery, no-checkout-edit acceptance, registry persistence across view changes, migration, cancellation, recovery and replay guards. |
| Design docs | Update Executable Components, Personal Lenses, Extensions, Astra Harness and relevant object/spec sections with verified support and remaining limits. |

This is a substantial application/runtime change, not a root flag or a wheel
patch. Implement it through runnable vertical slices: native UI/world bridge;
packages and independent tools/data; authored shell/conversation/skills; development
feedback and lifecycle hardening. Keep demos usable between slices. These are
dependencies for this implementation proposal, not a fixed M2+ product roadmap.

## Acceptance for the first complete delivery

With the host repository fixed after implementing the platform support, JEFF must:

1. Add pointer-anchored mouse-wheel zoom to the existing notes experience, with
   smooth local input, optional persisted view state and unchanged note contents.
2. Change the chat panel's position, styling and message presentation through a
   native package, preserving the conversation and unsent drafts.
3. Build an independently installed notes tool and invoke it after switching to
   another view, without restarting JEFF.
4. Create and use an application facet type and a reusable skill, then revise the
   tool/skill during the same session without editing host code.
5. Preview a broken revision, identify its error, retain a usable installed view,
   and restore a previous version through independent recovery.
6. Rebuild the resulting world from events with identical durable state and no
   executable code or model requests rerun by replay.

These examples are platform acceptance tests, not features to hard-code for JEFF.
Include a further interaction chosen after the implementation to check generality.

## Limits and long-term direction

A general programming runtime over a broad world API can express an enormous
range of applications. It cannot manufacture a missing hardware, operating-system,
network or provider capability. External integrations need generic host adapters
such as HTTP, authorized file access, media or process execution, exposed through
the same capability broker when intentionally introduced. Mark that distinction
clearly in refusals: implementation missing versus authority missing versus an
unsupported host capability.

Keeping source, definitions, installations and dependencies native gives future
devices and social spaces something concrete to copy, inspect and run. Grants
can later differ per world, person or package without replacing the programming
model. Portability remains conditional on the target device's runtime and adapter
support; schemas, references and code alone do not solve synchronization, conflicting
edits, service placement or resource limits. Do not import shared packages with
the local development owner's standing authority automatically.

Direct repository editing remains an emergency platform-development workflow,
separate from JEFF's normal abilities. Broad application control should survive
turning that emergency workflow off.
