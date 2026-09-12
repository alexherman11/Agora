# Decisions

Each entry records a choice and its reason. Implemented behavior is recorded in
[Implementation Status](docs/Implementation%20Status.md).

- **2026-09-06 — Fresh implementation.** Use branch Agora3 and a clean current
  document set, with no runtime imports or compatibility dependency on earlier
  implementations.
- **2026-09-06 — Unified direction.** Native development and a Linux VM are parts
  of one operating environment. Native packages preserve meaning and reuse; the
  guest supplies general execution.
- **2026-09-06 — Broad development delegation.** The operator can delegate broad
  local-world and guest authority to JEFF. Per-feature confirmation is not the
  default development workflow.
- **2026-09-06 — Programmable shell.** Chat, composer, desk and inspectors belong
  to the native application layer. Host recovery remains independently usable.
- **2026-09-06 — Asynchronous development horizon.** JEFF should remain available
  to the person while a development worker builds, tests and debugs a candidate.
  Worker implementation is deferred. Model choice is configurable and must be
  evaluated; GPT-4 is a user-suggested candidate, not a required dependency.
- **2026-09-06 — Initial tooling.** Use Python 3.12+ and uv for the host skeleton.
  The guest distribution, hypervisor, UI build tool and package execution runtime
  remain open. A development toolchain choice is not an OS architecture guarantee.

- **2026-09-06 — Adapt the established documentation.** Preserve the Constitution,
  master Spec, Reference and Essays structure, including detailed examples and
  schemas. Correct conflicts in place. Consolidate the VM and authored-development
  direction in [Native Development](docs/Reference/Native%20Development.md), rather
  than replacing the whole design with a smaller set of summaries.
- **2026-09-06 — Constitutional record scope.** Clarify Article V.1 of the
  unratified draft: native event history reconstructs native state, not arbitrary
  guest files or external reality. Preserve the rights, daemon, governance,
  stewardship and amendment text. This is an explicit draft clarification, not
  a claim that a constitutional ratification or amendment vote occurred.
- **2026-09-06 — Reuse the extension model.** A native source package is an
  executable extension, with separate source/build/installation identities.
  Avoid creating a parallel application ontology.
- **2026-09-06 — Demonstrate authority at its actual boundary.** Broad guest-root
  development does not establish per-package isolation or arbitrary data-flow
  tracking. The host gateway protects canonical native records; scoped/shared
  execution must demonstrate its stronger boundaries separately.

- **2026-09-06 — Capability creation is the primary development test.** JEFF must
  be able to author missing inspectors, computations and development tools during
  a session. Prefer native declarations and bindings, retain executable package
  content when necessary, and keep general guest instrumentation available. A
  missing tool alone must not require a platform repository change.
- **2026-09-06 — Facet dependencies are native intent.** Add explicit bindings to
  versioned authored transformations, with one definition per target and derived
  effective values. Relative placement is a worked example, not a platform special
  case. Dependency invalidation, manual edits, cycles, restart and failures must be
  specified and tested before calling the capability implemented.

## Architectural decisions to validate

- **2026-09-06 — Build a working native-development bootstrap.** Use a protected
  Python host gateway with a transactional SQLite journal and derived object
  cache. Preserve one authenticated write path, full replay without execution,
  object revision checks and whole-batch validation. The journal and cache share
  a database in this slice; separate payload retention and erasure remain work.
- **2026-09-06 — Real Linux with a separate candidate yard.** Provision dedicated
  VirtualBox Ubuntu 24.04 guests from a pinned, verified image. The main guest has
  broad root access. Reset a distinct VM before every Python build or candidate
  exercise; it has no live native token. A shared root VM with live credentials
  cannot also promise that candidate code cannot write the live world.
- **2026-09-06 — Native guest programs can use the world.** A pinned SSH reverse
  tunnel exposes a narrow authenticated native RPC listener to the main guest.
  The Python client lets authored programs create data, revise packages and call
  installed tools. Host recovery and model/account endpoints are excluded. A
  durable authority generation invalidates old clients; commit and revocation
  serialize across host processes, rather than relying on cached permissions.
- **2026-09-06 — Keep the human orientation and native skills separate.** Include
  Alex's supplied JEFF orientation with accurate early-runtime grounding. Reuse
  the managed OpenAI-account Codex SDK path and its tested tool isolation. The
  model adapter remains host-side for now; Linux supplies broad execution.
  Authored skills are versioned native package files, not arbitrary notes promoted
  into the human's prompt. Asynchronous worker agents remain a later capability.
- **2026-09-06 — Make the supplied shell a native package.** Serve the installed
  self-contained HTML source for desk and chat in an isolated browser frame.
  Keep operator recovery outside it, keep chat records independent of its lifetime,
  and flush pending note/draft edits before replacing the frame. Pointer motion
  belongs in view state; completed positions enter native history.
- **2026-09-06 — Pin source without overstating builds.** Retain source, manifest,
  digest, runtime contract and base installation revision in native build receipts.
  Python builds currently prove syntax in the reset yard; browser builds admit
  the HTML entry. Neither proves user interaction or freezes all main-guest
  dependencies. Exercise behavior and record that evidence separately.

- **2026-09-06 — Everyday authorship and product quality.** Use explicit memory,
  the growing AlexBench collection and a compact native music sidebar as concrete
  capability-creation examples. Memory and work products have distinct retention
  and retrieval roles. JEFF should leave usable tools for smaller agents, and
  application customization must preserve coherent design and interaction quality.
  Provider integration requires its own evidence; these examples are not claims
  of working applications or a request to replace the person's system prompt.

- **2026-09-06 — Defer external-effect uncertainty.** At the person's direction,
  do not make receipt infrastructure, remote deduplication or uncertain-outcome
  recovery part of the current development work. Prioritize JEFF's ability to
  create tools, bindings and programmable behavior. Retain the reference contracts
  as future design, without claiming those guarantees are implemented.

- Place the authoritative world service outside guest-root authority. This is
  the baseline design; prototype the connection and lifecycle before claiming it.
- Select a reproducible Linux image and deployment recipe. Evaluate a declarative
  configuration system without coupling native object formats to its syntax.
- Decide how execution artifacts and background-job checkpoints are retained.
- Choose browser/UI and headless package runtimes and their versioned contracts.
- Specify crash recovery, event framing and cross-version storage compatibility.
- Decide which external capabilities the first VM experiment actually requires.

## 2026-09-07 — Chat visibility

- Render assistant Markdown with pinned, vendored Marked 18.0.12 and DOMPurify
  3.4.15 under a restricted presentation allowlist. No network dependency at render.
- Aggregate assistant item/phase snapshots independently of the diagnostic event
  tail so polling cannot drop text. Keep intermediate progress transient and final
  answers durable. Show tool names and elapsed time without raw command output.

## 2026-09-09 — Vision-led docs and the presentation checkpoint

Alex asked to represent all review suggestions or remove limiting requirements,
keep documentation focused on vision and existing structure, then checkpoint
current work. The old design is retained in Git history; current notes are
self-contained and the 56-entry review has a coverage map. Speculative solver,
storage, worker, federation, publishing and governance rules are options rather
than universal obligations. Current native authority/replay/recovery boundaries
and the exact runtime guide remain explicit. This changes no license instrument.

The checkpoint also retains the existing native runtime/chat work and a compact
archive of the isolated presentation experiment, including JEFF's final package
and the post-comparison human-UI repairs. It does not modify the main installed
world. The next requested work is five comparative application-development rounds
with two independent worldlines per variant and correctness-led winner selection.
See docs/Implementation Status.md and experiments/visual-presentation/README.md.

## 2026-09-10 — Restore depth without restoring dogma

The September 9 compression removed false universal requirements, but it also
removed ordinary-life workflows, failure cases, alternatives, open questions and
the moral rationale needed to understand why Agora exists. Restore the detailed
Constitution, master Spec, Essays and References as the active documentation on a
new `agora4` branch. Preserve the September 9 corrections by explicitly classifying
claims as durable commitments, current invariants, tested behavior, candidate
mechanisms, open questions or rejected universals. Git history is evidence, not a
substitute for keeping important rationale readable in the current tree.

The restored Constitution is an unratified moral charter rather than a fixed
technical or legal constitution. It retains personal direction, loyal JEFF,
anti-surveillance, provenance, recovery, practical exit and accountable shared
power while leaving schemas, runtimes, licenses, governance structures and agent
topologies revisable. [Design Commitments](docs/Design%20Commitments.md) is the
status key for the restored documents; [Implementation Status](docs/Implementation%20Status.md)
remains the dated evidence inventory.

Carry forward Personal Lenses, Executable Components, Astra Harness and the
Security Addendum from the older `docs` branch as explicitly labeled prototype
lineage. Their implemented results and boundary lessons are important design
evidence, while their operation names, module paths and limits do not describe the
Agora3 runtime unless revalidated there.

## 2026-09-10 — Independent browser applications experiment

- Separate package release, subject identity and open appearance. Notes and
  Documents can edit one object without copying data or sharing browser globals.
- Use a generic desktop and a small subject-bound browser protocol. App methods
  pass through existing native commits; guest-root authority is a separate scope.
- Retain drafts/selection per appearance, pin running code, and flush before
  replacing or closing a view. App installation alone does not reload siblings.
- Author a shared editor/annotation contract once and vendor it into releases.
  Defer a runtime dependency resolver until an observed need justifies it.
- Export only installed application source/manifest/digest. Disable applications
  without deleting content/schema/state; refuse implicit schema migrations.
- Keep this experiment on its own branch and world. Its tested browser boundary
  is not a full migration of the research Desk or a multi-user permission system.
  See docs/Reference/Application Experiment.md for checks and limitations.

## September 10, 2026 — Resident continuity and first-party extraction

- Name the continuing resident JEFF0 and preserve the exact durable model-thread binding across service runs; a failed resume must refuse rather than silently start another identity. The previous ephemeral context is unavailable, so its full native transcript and authored checkpoint form the initial handoff.
- Carry existing discussion object IDs, original anchor evidence and unfinished drafts into independent Documents views. A bounded declared subject-linked collection and the public editor selection contract provide the required composition without importing editor internals.
- Declare Markdown/source semantics and UTF-16 object/revision/hash selections explicitly. Shared storage does not authorize silently changing editing semantics, and a refresh must never overwrite another view's unsaved draft.
- Treat this migration as trusted first-party extraction. Browser capability tests do not establish safe installation of arbitrary untrusted applications or isolation of root-capable guest packages.

## September 10, 2026 — Agora4 integration and authored orientation

- Merge the application runtime into Agora4 while retaining its restored Constitution, full specification, essays and design references. Keep current APIs and evidence in Runtime Guide and Implementation Status rather than replacing the design vault with implementation summaries.
- Restore Alex's original three-paragraph JEFF orientation verbatim; maintain current runtime guidance separately. Compose both files into base instructions because a compiled-runtime probe found that changed supplemental developer instructions were omitted on the first resumed turn. Preserve the resident's exact conversation instead of resetting it to update the prompt.
- Point the canonical JEFF0 launcher at Agora4 source while retaining its world path, guest machines and durable conversation binding. A branch integration changes code provenance, not ownership or identity of the existing world.

- **2026-09-12 — Isolate the parallel prototype.** Fork the native database, managed
  conversation, source and both VMs; preserve the original launcher and world.
- **2026-09-12 — Separate commitment, attempt and adoption.** A durable task owns
  versioned intent; a worker edits a scoped candidate. Ready is not installed.
  Adoption checks current inputs and prerequisite results atomically.
- **2026-09-12 — Bound execution and expose contention.** Two worker slots, explicit
  resource leases and visible wait reasons keep independent conversation useful.
  Interrupted attempts require explicit retry; budget exhaustion is not success.
- **2026-09-12 — Route reports without widening authority.** Linked tasks exchange
  public reports, current-brief messages can steer a running worker, and important
  events wake JEFF. Routine evidence stays inspectable. Never hold world authority
  while waiting for another runtime to accept a message.
- **2026-09-12 — Preserve revised intent.** Old messages remain in history but are
  excluded from the new brief's working context. Adopted task-owned outputs are
  baseline inputs to later attempts rather than permanent write-once names.
- **2026-09-12 — Preserve protocol failure distinctions.** Tolerate newer runtime
  history/envelopes through narrow identity/payload adapters; actual failures,
  time limits and cleanup failures cannot produce a ready worker result.
- **2026-09-12 — Compact voice footer.** The prototype chat reserves a footer
  rectangle for host-owned voice controls and places work status underneath.
  Microphone access and call actions remain in the host; closing chat restores
  the independent Voice control. The live shell package was installed without
  restarting the service. Isolated browser checks cover docking, close/reopen,
  laptop width and call-control layout; live refresh verification is blocked by
  a separately observed executive follow-up/chat-lock deadlock.

- 2026-09-12: Keep Agora4 in a standalone checkout, preserving the existing parallel Desk world in place. Never wait for runtime steering while holding the chat callback lock: a live thread dump confirmed that cycle blocked all history HTTP slots. Typed, voice and worker follow-ups release the lock before steering.

- 2026-09-12: Preserve metadata-only voice failure diagnostics (operation, exception class, close codes and stack locations) in status and local service logs. Generic disconnect messages hid repeated result-delivery failures; never log audio, transcripts, exception text or credentials.
