# Architecture

Status: design baseline to validate. No VM or world service is implemented yet.

## Three cooperating parts

**The protected host** owns the authoritative world gateway and event storage,
identity and delegation checks, credential references, VM lifecycle and independent
recovery. It is deliberately small and non-agentic. Its authority is not writable
by a root process in the guest.

**The Linux workspace** runs the desktop, JEFF's execution environment, package
builds, applications and background services. The operator may grant JEFF root
inside this guest. Guest administration does not mount host credentials or the
authoritative world directory as writable files.

**The native application layer** consists of object data, source packages,
installations, skills and application schemas. Host services materialize its
state; runtimes execute its packages in appropriate guest or browser surfaces.
Its contracts do not depend on one Linux distribution or display technology.

The agent loop and execution may live in the guest. Hosted model inference is
a separate service. The placement of the model connection must preserve provider
authentication without copying secret tokens into world objects or VM templates.
The exact authentication transport is an implementation decision.

## State ownership

| State | Owner and persistence | Recovery meaning |
|---|---|---|
| Object identities, facets, package source, installation choices, conversation records | Native event history and retained payloads outside guest-root authority | Replay native state without execution |
| Packages, service definitions, startup and OS configuration | Versioned machine recipe and pinned build inputs | Rebuild a compatible guest |
| Guest files and legacy application data | Guest resources, with explicit retention/import/export arrangements | Restore a consistent resource backup or retained artifact |
| Processes, connections, current device state | Live guest or external environment; observed into the world | Reobserve or deliberately reconcile |
| Model transport state and credentials | Host/provider services | Reconnect using current authority, never replay a credential |
| VM checkpoints | Supervisor-controlled storage | Restore captured machine state; coordinate with world history |

A world branch and a VM checkpoint are separate things. If a checkpoint is restored
while the world stays current, the guest must reconnect and reconcile against that
current world. In-flight job IDs and stale writes are checked. If both are restored,
the supervisor coordinates their branch/checkpoint boundary without restoring
revoked authority or forgetting completed external effects.

## Native changes and machine changes

Native edits enter one authenticated verb gateway. Program execution can request
world mutations through that gateway; programs cannot access the host's SQLite
connection or append directly to its log.

Guest execution is deliberately broader. JEFF may install software or modify a
guest file without a semantic adapter for that operation. Record the requested
execution and its observed outcome, and distinguish these machine changes from
native state. A shell transcript does not make a filesystem reproducible.

Useful experiments should be captured as package source, dependencies, a machine
recipe or an installed service. Native import/export operations may connect
retained guest artifacts to objects without pretending every file is already one.

## Runtimes and surfaces

UI packages execute in browser documents with ordinary browser input and rendering.
They access world services through an authenticated bridge. Headless package
actions run in supervised processes/workers with an explicit runtime contract.
The desktop may also host conventional Linux applications.

Root inside the guest is an experimental capability, not a claim that every
guest process is individually isolated. Host separation is the important first
boundary. Per-package isolation can become stricter without changing native
object or installation identities.

A browser sandbox is not a guarantee of independent CPU scheduling. Recovery
must be reachable from the supervisor when an authored page or guest is stuck.

## Desired and observed machine state

A service definition records desired configuration. A controller observes the
guest and drives it toward that configuration. Observations carry the desired
revision, observation time, source incarnation and freshness. “Starting,”
“running,” “failed,” “blocked” and “unknown” are distinct outcomes.

Repeated reconciliation must be convergent. One-time effects such as publishing,
sending a message or paying are explicit operations with retained identities
and receipts. They are never retried blindly by replay or ordinary reconciliation.

## Rebuildability and distribution

Agora uses Linux as an execution substrate. This plan does not require writing
a kernel, replacing device drivers or inventing a new general-purpose scheduler.
Its operating-environment contribution is the relationship between native meaning,
programmable behavior, conversation and control of a real computer.

The portable unit is native data plus source, pinned dependencies and a machine
recipe. VM images provide convenient execution and checkpoints, but are not the
only export format. A fresh compatible machine should be able to assemble an
installed capability without JEFF recreating undocumented manual steps.

Linux distribution, hypervisor, image format and runtime choices remain open.
The first machine need not solve graphics acceleration, audio, mobile devices,
cross-architecture binaries or remote latency for every target.

A participant's guest root does not confer room administration. Shared objects
and services have their own authority; disconnected behavior, conflict resolution
and service placement require explicit future contracts.

Not every device needs a full VM. A capable machine can host execution while a
browser or smaller device provides a view and input. That arrangement must make
latency, disconnection and unavailable capabilities visible rather than pretending
all devices have identical resources. Local execution can remain useful when a
remote service is unavailable.

Rooms should connect people's environments without turning them into one shared
root account. Shared data, installed programs, personal views and service ownership
are separate choices. Package portability does not solve data synchronization;
replaying one local log does not solve concurrent multi-person edits. Before
distribution, specify identity resolution, causal/conflict semantics, compatibility
and the authority that accepts shared changes. The first local implementation
should avoid assuming that one global event sequence will own everyone's world.
