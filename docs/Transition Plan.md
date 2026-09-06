# Transition Plan

Status: implementation plan for a new codebase. Only the skeleton is built; see
[Implementation Status](Implementation%20Status.md).

## One project, small proofs

Native development and the VM belong to one architecture. Building them as a
single large undemonstrated release would make failures difficult to locate.
Use a few runnable slices to establish the boundary and the development loop.

The slices below express immediate dependencies, not a complete product schedule.
They can be combined where a smaller executable proof is possible. The longer
horizon is a set of desired capabilities, not a numbered build order.

## First slice: a protected native world

Implement a minimal host world service: stable identities, typed facets,
authenticated verbs, retained event payloads, derived read state and replay.
Provide direct inspection and the smallest useful command-line client.

Prove that successful native changes survive restart, replay reproduces the
current state, invalid changes append nothing, and clients cannot write storage
directly. Define crash recovery and storage versioning as part of this slice.
Implement the storage model before assuming a UI or an agent makes it correct.

Choose a small initial vocabulary; application facets must have an explicit path
to native definition. Do not turn every prospective application into a host type.

## Second slice: a controllable, rebuildable Linux workspace

Select a hypervisor and Linux image using an actual local prototype. Evaluate
startup/rebuild time, automation, resource cost, display/input delivery and recovery.
Keep the machine recipe versioned. Do not require a custom Linux distribution.

Add supervised lifecycle, a console, guest execution and an authenticated
connection to the host gateway. Grant the development session broad guest-root
and local-world authority. Keep authoritative storage and credentials outside
guest-writable mounts.

Prove guest administration and a native edit through the bridge. Break the guest
UI, recover from the host, revoke its session and verify that stale credentials
cannot mutate the world. Rebuild the guest from its recipe. A checkpoint alone
does not satisfy the rebuild exercise.

Model authentication is a separate integration check: preserve the person's chosen
account-based path where supported, and demonstrate an actual authenticated call.
Do not copy credentials into a package or VM image or substitute a different
billing/authentication path without the person's direction.

## Third slice: one native development loop

Implement package source editing, one build/runtime contract, pinned installations,
a headless action registry and one browser mounting contract. Add the minimal
application schema and live query support needed for a useful application.

Connect JEFF to discovery, native editing, builds, diagnostics and candidate
interaction. Job identities, results and cancellation should survive UI replacement.
A second development agent is not required for this slice.

The demonstration is a note board whose dragging JEFF authors as package code.
JEFF then authors a distinct interaction, such as wheel zoom or grouping, without
adding a feature-specific platform case. This establishes invention beyond a
predefined menu of behaviors.

## Fourth slice: a programmable everyday shell

Make the desk and chat native packages on the same runtime. Store conversation,
drafts, active work and installation choices independently of disposable views.
Retain direct host recovery and a known working shell.

Prove that JEFF can change chat layout and behavior without losing a draft,
restarting a model operation or duplicating tool effects. Exercise failures and
the route back to a working interface. Build native editing and inspection so
the person can also understand and change what JEFF installs.

This completes the first coherent environment. Do not expand the social or
device platform until the basic experience is useful and recoverable.

## End-to-end acceptance exercises

| Request or condition | Evidence needed |
|---|---|
| “Let me drag notes around” | Real pointer input, durable final placement, no event per motion frame |
| “Now add a different interaction” | Authored package change using the same platform, exercised in the browser |
| A note is created after the lens is installed | Live membership updates without rewriting the binding |
| “Add a review state to these notes” | Native schema definition, validation, generic inspection and replay |
| “Give yourself a tool for this” | Installed action discoverable in the same JEFF session, callable with its view closed |
| “Update the way you handle this task” | Inspectable skill revision applied at a defined context boundary |
| “Move and change the chat” | Conversation, draft and running work survive shell replacement |
| A candidate fails or is stale | Working installation retained; clear diagnostics; no overwrite of newer work |
| The guest is stuck | Host stop/recovery works independently |
| A compatible machine starts fresh | Native state and installed capability restored from retained data, source, dependencies and recipe |

These are future acceptance criteria, not completed tests. The exact first
application may change if another example tests the same architectural questions
more effectively.

## Feature horizon, without a build order

- **Asynchronous development workers:** JEFF remains conversational while a worker
  builds, tests and debugs; tasks can be steered, cancelled and safely adopted.
- **Richer native applications:** reusable components, richer data types, service
  composition, broader development tools and useful legacy software integration.
- **Social spaces:** shared objects and programs, presence, invitations,
  collaboration, provenance and explicit administration.
- **Multiple devices:** remote access, synchronization, offline work, placement of
  computation, device-specific input and appropriate views of the same objects.
- **Distribution:** portable worlds and packages, dependable installation,
  compatibility checks, dependency retention and economical deployment.
- **Accessible interaction:** keyboard, screen-reader, voice and other input
  paths that remain useful as people customize the shell.
- **Progressive authority:** narrower delegations, stronger package isolation,
  external connectors and explicit sharing controls.

For each expansion, identify a user experience, the smallest supporting mechanism
and an observation that could disprove the design. Investigate rather than assign
speculative dates or treat this list as a mandatory sequence.

## Decisions to make through use

Can the protected host remain small while generic guest execution handles unfamiliar
work? Can packages preserve reproducibility without making a simple customization
feel like release engineering? Does the object model remain clear when one entity
has many applications and appearances? Does conversation stay responsive during
long jobs? Can useful capabilities move between compatible machines?

Record results in [Decisions](../DECISIONS.md). Those results should shape the next
slice more strongly than a milestone number.
