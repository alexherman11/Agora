# Agora3 development guide

Agora3 is a fresh implementation of a programmable computing environment.
Read [Start Here](docs/Start%20Here.md), [Constitution](docs/Constitution.md),
[Agora Spec](docs/Agora%20Spec.md), the relevant reference contract, and
[Implementation Status](docs/Implementation%20Status.md) before domain work.

## Working agreement

The person directs the project. Design documents are revisable plans; tests and
working behavior support implementation claims. Explain conflicts and revise
the relevant contract when evidence changes the design. Do not invent approval
requirements for routine work already authorized by the person.

Preserve the Constitution → master Spec → References → Essays structure. Keep
worked examples and schemas beside their contracts. Prefer targeted corrections
to a wholesale rewrite; consolidate new directions where they have one owner.

Keep current design self-contained. Historical rationale belongs in Git history
or dated decisions; current documents must not require obsolete specifications
to resolve their meaning. Record new architectural decisions and evidence.

## Architecture boundaries

- Authoritative native-world changes enter one authenticated verb gateway and
  append durable events. Materialized tables and indexes are derived.
- Guest root applies to the Linux workspace. It does not control host credentials,
  the authoritative world service, host files or recovery.
- Arbitrary guest files, processes and external systems are not covered by the
  native-world replay guarantee. Model them as resources with observed status.
- Replay restores recorded state; it never executes programs, sends messages,
  invokes models, restarts jobs or repeats external effects.
- Applications, UI, tools, schemas and skills are versioned packages/objects.
  JEFF develops them through native operations. A guest-machine execution
  capability supports experimentation without making opaque commands native facts.
- Derive human actions and JEFF's tools from one installed-capability registry.
  Visibility of a lens does not determine whether its tools exist.
- The shell, including chat, is programmable. Independent host recovery remains
  available when the authored shell fails.
- Broad operator-selected development delegation is the initial direction.
  Do not build a detailed multi-user permission system before it is useful.
  Do preserve caller identity, effective delegation and the host/guest boundary.
- JEFF may eventually delegate work to asynchronous development agents. This is
  a documented horizon, not permission to add autonomous worker machinery now.

## Implementation practice

Prefer small runnable vertical slices. Keep host services and guest programs
separate in imports and deployment. Build the minimum host machinery necessary
for general capability; avoid new platform cases for individual UI requests.

Do not copy an implementation merely because it once worked. Reuse algorithms or
sections of prose when their contract remains appropriate, and verify them here.

Before calling a slice complete, update Implementation Status with the actual
checks and remaining limitations. For storage changes, verify replay equivalence,
failure atomicity and compatibility. For UI changes, test actual input delivery.
For runtime changes, enumerate effective tools and test the intended boundary.

Do not claim a running VM, successful model call or browser behavior from static
configuration or scripted model output. Source and dependency versions must be
pinned for execution. Credentials and private worlds are never committed.

The repository is currently a skeleton; proposed paths and operations in the docs
are design contracts, not importable APIs.
