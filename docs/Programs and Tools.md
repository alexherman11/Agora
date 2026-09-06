# Programs and Tools

Status: proposed native development model; no package runtime is implemented.

## The unit of authored capability

A native package is a versioned source object. It can contain named source files,
UI entry points, callable actions, assets, dependencies, schemas, skills, service
declarations and tests. These are optional parts, not a required mini-framework
for every button. A small package can be one file and one action.

JEFF reads and patches package source through native operations with expected
revisions. Package paths identify files inside the package, not arbitrary paths on
the host. Larger payloads can use retained content-addressed blobs whose reachability
is part of export and recovery.

This is executable code authored through Agora. The platform does not need a new
built-in verb for dragging, sorting, a timer or a domain-specific tool. Trusted
host capabilities still require platform implementation; a manifest cannot invent
access to hardware or a service the host has not exposed.

## Source, build, installation and state

These are separate identities:

| Concept | Meaning |
|---|---|
| Package identity | The enduring application or library |
| Source revision | Exact authored files and declarations |
| Build artifact | Immutable output with source, dependency and toolchain provenance |
| Installation | A world's selected artifact, configuration and registered capabilities |
| Instance | A particular view or service with its own identity and state |
| Invocation | One action using pinned executable inputs and recorded execution identity |

Builds take an immutable source revision and resolved dependency lock. Dependencies
include both package dependencies and external build/runtime inputs. Content hashes
and retained artifacts make “the version that passed” meaningful. They do not,
by themselves, prove a hermetic or reproducible build.

The first package dependency graph should be explicit and acyclic. Dependencies
resolve to exact revisions; ambiguity, missing dependencies and cycles are errors.
Running code does not switch dependencies halfway through a call.

Guest-root execution may install arbitrary tools for an experiment. To distribute
that experiment, capture its required environment in the package or machine recipe.
A build with uncaptured dependencies must report that limitation.

## Installed actions outlive open views

An action declares a stable qualified name, argument and result schemas, handler
entry point, requested capabilities and execution kind. Installation registers
actions whether or not any UI is open. UI entry points and action entry points
may share libraries and data without depending on a hidden browser tab staying alive.

Human controls, JEFF and package code discover the same installed registry. A
registry revision describes changes. JEFF refreshes discovery during its session
and can invoke a newly installed action without restarting the conversation.
Discovery and invocation may use generic platform operations; the model adapter
must not freeze the effective capability list at session startup.

Names are installation-qualified. Convenient aliases must refuse ambiguity.
Invocation resolves and pins the selected installation revision; if a caller
requires a revision that has changed, it gets an instructive stale-reference error.
An existing invocation finishes against its original executable inputs unless
explicitly cancelled.

Tools can call other installed tools. Composition preserves caller identity,
delegation, execution ancestry and budgets. It cannot gain authority by passing
through a more privileged package. Dependency cycles and recursive execution are
different concerns: runtime call depth and resource limits also apply.

## State has an owner

View preferences, application records, a service's configuration and a person's
conversation draft have different lifetimes. Packages declare which state is
instance-owned, shared application data or person-specific state. Closing a view
does not delete its notes or uninstall its tools.

Native state reads and changes use the common gateway. Ephemeral interaction state
stays in the runtime. Guest files require explicit retention arrangements.
Application schemas and live query bindings follow
[Objects and Queries](Objects%20and%20Queries.md).

## Activation and execution

A candidate points to an immutable artifact and reports its required capabilities,
state compatibility, dependency lock and test evidence. Activation atomically
updates the native installation record and registry. Runtime processes then
converge on that desired installation; “recorded as installed” and “healthy and
running” are separate states.

Activation checks the current installation revision and any state migration
preconditions. Unrelated new notes should not invalidate a tested layout. A stale
installation or incompatible data migration must not overwrite newer work.

A pure computation, a native transaction and an external side effect have different
failure semantics. A multi-step action is not automatically one database transaction.
Gateway transactions can be atomic; external work needs operation identities,
receipts and explicit treatment of partial or unknown outcomes. Replaying an
invocation record never invokes its handler again.

A service has durable desired configuration and observable execution status.
Closing its UI does not stop it. Uninstalling disables new invocations and explicitly
handles running work, mounts, dependents and retained state; it does not silently
delete application data.

## Evidence and portability

Tests belong to the package. Build logs, runtime errors, interaction traces and
screenshots refer to the artifact and environment that produced them. Test success
is evidence about those conditions, not proof that arbitrary authored code is safe.

An export can include source, locked dependencies, retained artifacts, schemas and
selected data. It excludes credentials and does not transfer the author's standing
authority. A recipient chooses where and with which capabilities to install it.

The first proof is deliberately small: a lens with an interaction JEFF authors,
plus a callable action that still works after the lens closes. A second, different
interaction should use the same runtime without adding a platform special case.
