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
