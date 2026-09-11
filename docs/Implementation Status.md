# Implementation Status

**Agora4 source, restored design and recorded evidence · September 10, 2026.**

This file is the evidence inventory, not a substitute for the restored design.
[[Design Commitments]] explains the difference between a durable commitment,
current implementation, tested behavior, candidate mechanism and open question.
[[Start Here]] routes the full vision and reference set. Documentation restoration alone does not advance runtime evidence;
implementation and checks are recorded separately below.

Documents explicitly labeled **prototype lineage** contain evidence from the
older `docs` implementation branch. They remain useful, but their results are not
counted as Agora3 runtime verification unless this file names a corresponding
Agora3 check.

## Agora4 integration

`agora4` combines its restored design vault with the implementation from
`experiment/native-applications` through `2a0e60a`, including the combined
improved-Desk runtime and independent Notes/Documents browser applications.
They share native content and an editor/annotation contract while keeping separate
frames, pinned builds, leases, drafts and appearances. Portable application
export/import and removal preserve user objects. Alex subsequently authorized
moving the existing resident, named JEFF0, into this application world. The move
preserves the original journal, conversation, documents, discussions, packages
and guest workspace. The old native world remains an archive.

Verification: 145 Python tests passed (two optional inventory cases skipped),
fresh and resumed compiled-runtime inventory cases passed separately with local
mock inference, and 28 real Edge browser checks passed across the independent
application lifecycle and migrated-world interactions. See [[Application Experiment]] for exact
scope, retained evidence and limitations, and `examples/native-applications/`
for runnable source. Existing research/packet actions and source remain installed;
their former composite UI has not been extracted into independent applications.

JEFF0 has a protected resident identity and exact durable model-thread binding.
Service restart resumes that thread; failed resume refuses rather than silently
starting a replacement. Copying a world does not transfer ownership automatically.
The previous ephemeral model context could not be recovered: the original native
transcript and JEFF0-authored checkpoint provide the initial handoff. Native replay
and model-conversation persistence remain different mechanisms.
The live handoff and an idle service restart succeeded: the same thread remained
bound, JEFF0 recalled the preceding exchange and confirmed that he was ready to
talk. These checks added four native messages and did not modify authored work.

The Agora4 merge also restores Alex's original three-paragraph JEFF orientation
from his September 6 request. Runtime guidance lives in a separate source file.
Both are loaded on fresh and resumed conversations. An actual compiled-runtime
test using local mock inference verifies that the first resumed request contains
the restored wording and current guidance while retaining preceding history.
The tested runtime omitted updated supplemental developer instructions on that
first resumed turn; composing the two files into base instructions resolved this
without resetting JEFF0. The live Agora4 source switch preserved the resident
binding and replay integrity; an open Notes appearance saved its view state during
the switch, so the journal was not byte-identical across the restart. JEFF0 then
acknowledged the integration on the same model thread, adding two native chat
messages without invoking tools or modifying authored work.

The sections below retain the September 9 checkpoint evidence. On this branch,
the combined runtime additionally includes scoped action dependencies, targeted
package source tools, ordered browser asset assembly and grouped candidate
checks. Their earlier VM/model experiments were not rerun for this browser-only
slice. General dependencies, multiple people and guest-package isolation remain
unimplemented; browser appearance identity is now exercised in the new slice.

## Current runtime

Agora3 has a local native-development runtime, not the whole operating environment
described by the vision. Exact operations are in [[Runtime Guide]].

| Area | Present behavior |
|---|---|
| Native world | SQLite event journal and derived object cache; atomic schema/revision-checked facet writes; replay/rebuild without execution. |
| Application data | Application schema admission, generic JSON projection, object-level revisions and register replacement. |
| Authority | Authenticated gateway, protected keep, current delegation and revocation outside native history; protected runtime facets. |
| Packages | Retained source/build/installation identities; browser-1 and Python-1; installed actions and skill discovery. |
| Execution | Broad root development in a dedicated Linux VM; native bridge over pinned SSH; distinct resettable candidate VM without live native authority. |
| JEFF | Managed host-side account/model adapter; native discovery/invocation and clock/composition tools; one foreground turn at a time. |
| Shell | Authored desk/chat in a browser frame; independent parent/recovery; installed source can differ from supplied source. |
| Interaction | Native note editing, retained unsent drafts, replacement-time flush, Markdown/progress support; authored dragging retained as an example and in the development world. |

## Important limits

Python actions currently receive a snapshot capped at 1,000 objects. Current
stale checks are object-level and action context uses a broad native watermark.
Browser entries are self-contained HTML; general dependency/module loading is
not implemented. Queries are bounded paginated reads, not subscriptions.

The main guest's mutable dependencies are not frozen by a package source digest.
Root-capable guest programs share the development authority boundary. A native
action's returned proposed writes are atomic; a guest program using the native
client can also issue separate commits.

Stopping a turn rejects later callbacks but does not undo completed changes or
terminate every independent guest process. Revocation blocks native commits;
VM poweroff stops that machine. Package restoration, native replay, guest reset
and external recovery have different scope. Multiple people, general bindings,
appearance identities, fine-grained merges, asynchronous task machinery, shared
rooms, witness memory and external-effect recovery are not established by this
runtime. They are directions to evaluate, not required implementation stages.

## Recorded verification

The September 6–7 runtime work recorded native transaction/replay tests, stale
and invalid batch rejection, schema admission, package lifecycle and activation
races, actual HTTP authentication/origin checks, revocation and independent
recovery. Guest probes covered pinned SSH, disabled host sharing, root execution,
bounded output, descendant timeout cleanup, poweroff/start and reconnection.
Candidate checks verified reset isolation and absence of the live native client.

The compiled Codex runtime inventory was checked separately using simulated
inference: the model tool surface contained native discovery/invocation and the
clock/composition facility, with ambient host tooling absent. Real account-backed
JEFF separately authored, exercised and installed a counter package and invoked
it twice. These are different evidence levels.

Live JEFF-authored dragging was installed and independently exercised with real
pointer input, persistence, editing and draft checks. The subsequent Markdown and
progress upgrade recorded 90 Python tests passing, with the optional runtime probe
run separately. Real Edge checks covered sanitization, incremental snapshots,
final deduplication, draft/focus continuity, shell replacement, reload and mobile.
The development-world shell at that checkpoint was source 12 / installation 9.

These are dated reports, not promises that every configuration remains healthy.
The supplied shell, archived examples and live installed source must be inspected
separately when making changes.

## Isolated presentation experiment

The September 9 experiment copied the current runtime and actually installed
shell into two synthetic worlds. The candidate added a native presentation package
and two surface adapters. Eighteen real JEFF turns covered nine matched requests,
including new arrivals, a second view kind, exact chat sizing, local override/undo,
mobile use, an impossible request and authored circle layout beyond the catalog.

Both variants completed the scenario requests. Summed request time was 1498.1s
for current-system JEFF and 740.6s for the prototype; source saves were 12 and 3.
One baseline time was recovered after a control-file sharing error. The discarded
initial harness-authentication attempt and preparation time were excluded. This
was one trajectory per variant, not a statistical benchmark.

Independent checks passed 58 baseline / 59 prototype assertions. Human testing
also found prototype selection loss, an incorrect registry lookup and a limited
preview. The post-comparison review build repaired those; real input verified
15-second selection retention, zero-write visible style preview, Keep/Undo and
draft continuity. A composer sizing defect had already been repaired by JEFF
during the measured run. The native inspector agreed with rendered desktop
geometry; circles still overlap stationary notes and can crowd as membership grows.

Source and compact evidence are in
[the presentation experiment](../experiments/visual-presentation/README.md).
It is an isolated example, not silently installed into the main development world.
General surface registration, subscriptions, large-world behavior, concurrency
and smaller-agent use remain unproven. [[Presentation and Operators]] describes
the narrower direction supported by the evidence.

## Running checks

From the repository root:

    uv sync --dev
    uv run pytest -q
    uv run python scripts/check_docs.py
    uv run ruff check .
    uv run ruff format --check .
    uv run agora3 --world worlds/dev verify

Live VM/model probes consume real resources and have separate explicit commands
in [[Runtime Guide]]. Private world databases, credentials, VM disks and detailed
account artifacts stay outside Git. A successful build does not replace actual
input, persistence or runtime-boundary checks appropriate to the change.
