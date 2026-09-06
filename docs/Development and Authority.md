# Development and Authority

Status: proposed development workflow and boundary. Enforcement is not implemented.

## A broad standing development profile

For early development, the person can give JEFF broad authority over the personal
native world and root inside its Linux guest. That includes authoring and installing
packages, introducing application schemas, changing the shell and skills, creating
tools and services, and using guest execution to explore unfamiliar software.

There should not be a platform permission invented for every feature. A general
package runtime plus broad delegated capabilities should handle most requests.
The person should not need to approve each routine step of an already authorized
development task.

Guest root does not include host-root access, host files, provider credentials,
the supervisor's recovery controls or administration of other people's worlds.
This is a concrete deployment boundary, not a promise that a prompt will keep
a powerful agent inside a directory.

## Identity survives broad authority

Every gateway request carries an authenticated caller and effective delegation.
Record the originating task and package revision where relevant. The operator
can revoke a development session from outside the guest; restoration must not
resurrect revoked access.

Initial authority can be a simple, explicit local development profile. Preserve
a place to narrow it without building a complete multi-user policy language now.
A package declares needs; it cannot enlarge its own delegation, impersonate the
operator or turn a skill edit into a host permission change.

Guest-root access means guest processes are not mutually trustworthy security
domains. Per-package attribution in that mode is useful provenance, but cannot
prove that another root-capable guest process did not impersonate one. The host
can enforce the guest/session's outer boundary. Stronger package isolation will
require separate enforcement when sharing or running less-trusted software.

## One development loop

The normal path is:

1. Inspect relevant objects, package source, installed tools and current behavior.
2. Edit a candidate from an identified base revision.
3. Build it with recorded inputs and collect useful diagnostics.
4. Exercise it in a disposable world branch or isolated test state.
5. Inspect runtime errors, browser state, screenshots and interaction traces.
6. Activate the tested artifact against the expected live installation revision.
7. Observe startup and health, and retain a route to the previous installation.

The candidate receives explicit test capabilities. Pure UI and native-state tests
should not need live external effects. A native world fork does not isolate the
guest filesystem or the network; experiments that change those need a disposable
guest or another actual execution boundary. Test isolation must be observable.

JEFF needs actual feedback: file/line build errors, structured runtime failures,
logs, screenshots, accessible interface inspection and real browser input.
Feedback refers to a particular source revision and environment. Static validation
must not be presented as successful interaction testing.

## Activation, failure and recovery

Activation checks the tested artifact identity, dependency lock, current
installation revision and required state preconditions. Routine changes to a
live collection need not invalidate a candidate; data assumptions used by a
migration do.

An activation record changes desired installation state atomically. The supervisor
starts the new version and reports observed health. It tracks old listeners,
subscriptions and jobs so a UI replacement does not duplicate an action or leave
invisible background work running. A failed startup can retain or restore the
previous working presentation while reporting the failure.

Keep code rollback, native data restoration and machine restoration separate.
Reinstalling old code cannot safely read incompatible new data unless compatibility
was established. A coordinated restore is an explicit operation, not an incidental
effect of selecting an older package.

Stop and recovery remain outside the authored shell and guest-root authority.
The first implementation must demonstrate this against a broken or unresponsive
guest. Resource limits for jobs and builds are adjustable, but stopping a runaway
process cannot depend on that process cooperating.

## General execution without losing the native direction

The machine-execution capability may run guest commands, install system tools,
inspect processes and modify guest configuration. Record its request, execution
identity and observed result. An interrupted command can have partial effects;
an absent receipt means unknown, not automatically failed or safe to retry.

Promote useful behavior into source packages, installation declarations, retained
assets or a versioned machine recipe. Once the required host mechanisms exist,
building an application should not require editing the Agora repository. Root is
a practical escape from an incomplete adapter vocabulary; native packaging is how
the capability becomes understandable, reusable and portable.

Some new capabilities will still require host development, particularly new
protected integrations, device support or stronger isolation. Report that boundary
honestly rather than describing general guest execution as control of every
possible computer or service.

## Later authority

Shared rooms, imported packages and remote workers should receive independently
chosen delegation. A local development profile never propagates through package
export, a social invitation or a query result. Detailed per-object grants,
multi-party administration and package isolation belong to the feature horizon;
the host boundary and authenticated write path belong to the first implementation.
