# Personal Lenses

**Implemented prototype contract — September 5, 2026.** This is the approved first
declarative extension after the M1 foundation; [[Executable Components]] extends it
with authored behavior. Companion to [[Objects and Facets]], [[Extensions]],
and [[Agora Spec]] §22. Future display control is a direction, not an implemented guarantee.

## The first request

“Make my notes readable as a compact list, with a preview when I select one.”

JEFF creates a `core.lens` definition as an ordinary entity, places it on the desk,
calls `preview_lens`, and calls `activate_lens` with the exact previewed revision.
The renderer implements a small vocabulary; the notes view itself is data authored
through the same verbs as other content. Neither the shell nor JEFF has a special
hidden operation that constructs the notes extension.

```json
{
  "version": 1,
  "title": "Notes",
  "source": {"scene": "ent_desk", "facet": "core.text"},
  "list": {"component": "list", "field": "core.name.name"},
  "detail": {"component": "text", "field": "core.text.text"},
  "density": "compact"
}
```

The initial renderer supports list/selection and text detail. Source is either a
scene reference with an optional required facet, or at most 200 explicit entity
references. A scene contains at most 1,000 appearances. Lists return pages of up to
100 rows using `offset`. Fields are `core.name.name`, `core.text.text`, `written_by`,
and `revision`. `list.secondary` accepts up to two fields. The latter metadata
describes the text facet when present, otherwise the name facet. Density is
`compact` (the tightest supported rows) or `comfortable` (roomier rows). Field names and components are validated; there are no
expressions, scripts, network requests, arbitrary HTML, or ambient filesystem reads.

## Drafts, activation, and restoration

`attach` accepts `expected_revision`; 0 requires an absent facet. A stale change
is refused before anything is recorded. Editing `core.lens` creates a new retained
definition revision. The active display continues using its pinned version until
activation. Existing note identities and contents never change when a lens changes.

`preview_lens(entity, revision?, selected?, offset?)` is read-only. Selection must
belong to the declared source after filtering. Detail uses the complete content,
not a short projection. Missing source scenes refuse; missing individual objects
are omitted. Normal read policy applies to the local world; this prototype does
not implement multi-user facet ACLs.

`activate_lens(entity, revision?, expected_revision?)` validates the definition and
bindings, then writes the desk's `core.display` facet as `{lens, revision}`. The
optional precondition refers to the current display facet revision. An empty entity
restores the default desk. `read(entity, facet_type, revision)` exposes retained
facet revisions. The shell's restoration control reads the previous display revision
and reactivates it with a current-state precondition. Restoration records a new
decision; history is never deleted. Definitions are pinned, while bound note content
remains live. Software installation and migrations are separate future capabilities.

The shell lets the person preview a lens object, activate it, inspect its definition,
preview its latest draft, restore the previous display, or return to the default.
Keyboard and pointer selection update JEFF's explicit selection context. Selection
is session-local interaction state, not an event stream. Activated definitions
survive restart; the view works when JEFF is unavailable.

The CLI can use every registered operation through `agora call VERB JSON`. JEFF's
tools are derived from that same registry. A second request such as “make the list
denser and show who last edited each note” updates the existing lens rather than
creating a new application or modifying repository source.

## Broad display authorship

The longer-term goal is relatively full control of the visible workspace by the
person and JEFF: layouts, navigation, typography, widgets, and the chat panel itself.
The first implementation changes only the workspace. The conversation panel remains
shell code; future view definitions can bring it into the same composition model.
This is a desired capability, not an obligatory next milestone.

A small recovery surface remains dependable independently of personal views: stop,
default-display restoration, and authoritative permission information. Layout editing
must not implicitly grant access to conversations, rewrite history, or authorize
sharing. [[Executable Components]] defines the implemented executable boundary;
this declarative runtime does not establish a general code sandbox.

## Current local boundaries

The shell binds to loopback, validates host and origin, bootstraps a local session,
and requires a mutation token. Actor identity comes from the server session, not
request JSON. This assumes the local OS user is trusted; it is not remote-user
authentication. Content is rendered as text under a restrictive content-security
policy. Recovery controls are outside lens definitions.

JEFF turns are serialized. Stop prevents later tool dispatch after the current
operation completes; it does not reverse completed writes or guarantee cancellation
of an already submitted provider request. The provider client has a bounded timeout
and no automatic retries. World content is separate from system instructions, which
reduces accidental authority confusion but is not an injection-resistance proof.

Imports default to the world's `imports/` directory. The operator may explicitly
configure `AGORA_IMPORT_ROOTS` using the platform path separator. A path provided
directly to the trusted CLI authorizes that exact file. Imports are bounded to 8 MiB
and resulting text is still limited to one million characters. Validation prepares
bytes without persisting them; rejected operations leave no imported blobs. Captured
file bytes are snapshots, not two-way live bindings. Protecting against a hostile
process with arbitrary host filesystem access requires a later OS boundary.

## Reliability contract and evidence

World operations share a reentrant lock across threads and cooperating processes.
Replay application checks its cursor transactionally; reads use a persisted byte
offset. Complete malformed records fail with recovery diagnostics. Appending after
an incomplete suffix seals it with a recorded hash; legacy unexplained sealed gaps
require investigation rather than silent skipping. A replacement store is built
before the old destination is replaced.

Interrupted recovery itself (for example, a second crash while sealing a torn suffix)
can require explicit investigation. These tests cover the named recovery cases;
they do not establish universal power-loss recovery or distributed-write safety.

Text sessions use revision preconditions. A stale flush retains the session's pending
text and refuses to overwrite current work. Exporting an anchor persists its CRDT
identity, recording a revision when necessary. Unresolvable anchors return their
retained revision. Full simultaneous CRDT merging remains a desired feature. Content
reads omit the storage-codec snapshot; history and the debugger retain it.

Validation covers invariants, the scripted JEFF authoring loop, and browser use.
[[implementation-validation-2026-09-05]] records the 99-test suite, model-off browser
restart, and both synthetic live trials, including the first trial's spacing mistake. None of these tests
alone establishes the larger claim that Agora makes a model more capable than a
competent conventional environment. That comparison remains an ongoing experiment.
