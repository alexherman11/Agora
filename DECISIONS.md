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

## Architectural decisions to validate

- Place the authoritative world service outside guest-root authority. This is
  the baseline design; prototype the connection and lifecycle before claiming it.
- Select a reproducible Linux image and deployment recipe. Evaluate a declarative
  configuration system without coupling native object formats to its syntax.
- Decide how execution artifacts and background-job checkpoints are retained.
- Choose browser/UI and headless package runtimes and their versioned contracts.
- Specify crash recovery, event framing and cross-version storage compatibility.
- Decide which external capabilities the first VM experiment actually requires.
