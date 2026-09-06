# Interface and JEFF

Status: intended experience and contracts. Asynchronous development agents are
a later capability, not part of the current skeleton.

## The shell is application content

The desk, windows, menus, inspectors, chat panel and message composer are native
application packages. JEFF can change their layout, behavior and styling through
the same development operations it uses for another application.

The initial interface should use ordinary browser rendering and input rather than
a fixed vocabulary of platform-defined widgets. A package can implement a canvas,
document, timeline, spatial board or another interaction with its own source.
The platform provides general mounting, input, lifecycle and capability bridges.

A person should be able to ask for wheel zoom, keyboard shortcuts, different
navigation, a relocated composer or a new view without each request requiring a
host code change. Native applications may coexist with conventional Linux
applications and their windows. Device integration still depends on actual host
and guest support.

## Interaction and durable state

Pointer movement, drag previews, animation and intermediate layout calculations
belong to the view. Meaningful completed changes enter the native gateway.
A drag typically records its final placement; a zoom may remain a local preference
or be deliberately saved. Do not emit an event for every input frame.

View-specific state belongs to an appearance or view instance. Domain facts belong
to their objects. The same note can appear at different positions in two views.
Queries keep live views current using
[Objects and Queries](Objects%20and%20Queries.md).

Keyboard navigation, readable controls and basic direct operation matter alongside
visual freedom. Interaction tests need to exercise real browser input, focus and
layout; a handler called from a unit test does not prove that a person can reach it.

## Chat is editable; the conversation survives it

Conversation records, message identities, tool results, development tasks and user
drafts must not be owned solely by a disposable UI component. The native model
stores the durable conversation; the runtime manages streaming connections and
current execution. Draft persistence and retention are deliberate person-specific
settings.

Replacing the chat package must preserve messages, pending work and the current
draft. The new view reconnects to ongoing activity instead of starting the model
again or replaying tool calls. Provider credentials and opaque transport sessions
stay outside editable conversation content.

The person retains an independent way to stop work, select a known working shell
and recover a world or guest from the protected host. A programmable shell is not
allowed to remove the only route back into the environment.

## JEFF uses the environment's vocabulary

JEFF's context presents relevant objects, installed capabilities and current work.
It uses the same underlying facts and action registry as direct human operation.
Summaries disclose uncertainty, freshness and omitted information.

The agent adapter controls conversation and model interaction. It does not import
private storage internals to manufacture extra application capabilities. General
guest execution is itself an explicit capability with honest scope.

JEFF's editable procedures, tool choices and replaceable agent behavior should
also have native source and version identities. They can evolve through the same
candidate workflow. Authentication, effective delegation and independent recovery
remain host responsibilities; editing the agent does not alter those boundaries.

The model and authentication provider are replaceable dependencies. Account login,
API credentials and model naming must be verified against the selected integration
when it is built; they are not properties guaranteed by these architecture docs.

## Skills are native procedures

A skill can contain instructions, examples, supporting files and references to
installed actions. It has source identity and a revision, and can be inspected,
edited and installed through the native development model.

Installing or updating a skill deliberately changes JEFF's selected procedural
context. Merely reading a note, visiting a page or receiving package output does
not promote that content into trusted instructions. Skills can request tools; only
the effective delegation grants authority.

Skill changes apply at defined context boundaries. Ongoing tasks retain the
instruction revision they started with unless deliberately updated. Avoid an
invisible global prompt that changes underneath every running operation.

## Development as asynchronous work

The long-term experience is conversational JEFF supervising a development worker.
JEFF remains present while another agent edits code, builds, interacts with a
candidate, inspects results and debugs. The worker can use a different model;
selection should follow evaluation of that role rather than a fixed model name.

A development task is a durable native object containing:

- The person's request, acceptance examples and current clarification.
- Target package and base revision, candidate workspace and relevant inputs.
- Delegated capabilities, resource budget and cancellation identity.
- Status, progress, produced artifacts, test evidence and unresolved problems.

The task owns its work independently of an open chat window. JEFF can answer
questions, explain progress, adjust the brief or cancel it. A change in intent
must reach the worker; outdated output cannot quietly activate after cancellation
or a conflicting edit.

The worker's normal result is a candidate and a readable account of what changed
and what was exercised. JEFF can activate it under the person's standing
development delegation. The architecture does not require approval for every
routine package edit. More autonomous activation can later be explicitly included
in a task's delegation.

Concurrent workers need isolated candidate state and conflict checks. They must
not race to patch the same live package or assume that broad local authority makes
their intentions compatible. Cancellation is cooperative where possible and
supervisor-enforced when necessary; already completed external effects remain real.

## Build the lifecycle before adding agents

The first development loop can use one agent and supervised asynchronous jobs.
Keep job identity, progress, results, cancellation and reconnection separate from
a single model turn. That creates a useful path toward a coding worker without
implementing a multi-agent scheduler now.

The target interaction is simple: while a worker develops “let me group notes by
topic,” the person can keep talking to JEFF, edit a note, or change the request.
The resulting candidate respects those changes and does not lose the conversation.
