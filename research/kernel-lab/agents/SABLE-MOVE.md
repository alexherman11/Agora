# Sable's reviewed move

Builder draft, 28 October 2026. Implements the current resident card's next action:
Sable only, with owner activation after source review. Pike remains a second run
after Sable's real reply is verified. Nobody else is invited or woken by this code.

## What is ready

`move_resident.py` validates a review manifest and installs it through kdesk's
explicit `--resident-manifest` startup option. Normal startup changes nothing
about residents. Sable receives a member account (not a steward), a distinct
person session, her soul, the resident T2 charter, a private chat with Alex,
and a House configuration with `next_steps=on`, `wake_policy=addressed`,
`want=asleep`. There is no fallback provider or old-card import.

The soul and charter belong to Sable's closed group, led by Sable and JEFF;
Alex retains steward access. Only those three can change the soul. Source text
is copied exactly, with source, source author, approval, review attribution and
SHA-256 recorded separately from the kernel's import authorship. Later resident
writing stays intact on reruns. A different source or hash refuses the import;
an ambiguous person, house-agent or session also refuses instead of adopting it.
Session creation is confined to the explicit reviewed startup path and never
replaces an existing credential. A crash after the world record but before
session persistence is recoverable by rerunning the same manifest.

House uses the existing person session and transports. Addressed residents do
not start a model at startup or configuration changes, and task changes do not
wake them. An addressed chat message, explicit `house.wake`, or pending addressed
message on restart can start a turn. Every wake still reads their own current
`rows nextsteps:<person>`. Compaction uses the existing read-only charter/task
hook and the existing continuation within the addressed conversation. There is
no new timer or polling path. JEFF retains his existing event-driven policy.

## Review manifest and source limits

No actual soul has been exported or imported by this worker. Obtain only Sable's
approved soul through the archive's authorized reading interface; do not read
pickles or exported transcripts. Inspect its source and access policy before
export. The owner must resolve any private or ambiguous material before placing
it in a manifest. Preserve the original and its authorship. Store actual manifests
outside source control, under the owner's protected world data.

The live JEFF charter read on 28 October still contains the pre-T2 gaming and
ending-program rules. Do not copy that charter into this manifest. Supply the
reviewed resident T2 rules, including the approved program-ending change and
removal of the gaming rule, from MOVING-IN.md. The importer checks structural
approval metadata and hashes; it cannot prove a human reviewed the prose.
The reviewer must inspect the exact manifest text. It never rewrites Alex's
words or moves Sable's own lessons for her; she and JEFF can organize those
under “Before the move” later.

The JSON schema is intentionally narrow:

```json
{
  "resident": "Sable",
  "reviewed_by": "Name and dated owner review reference",
  "soul": {
    "source": "Exact approved archive soul reference and revision",
    "author": "Original authors, including Alex and Sable as applicable",
    "approval": "T3",
    "text": "Exact reviewed source text",
    "sha256": "SHA-256 of the UTF-8 text field"
  },
  "charter": {
    "source": "MOVING-IN T2, exact reviewed resident rules reference and revision",
    "author": "Alex",
    "approval": "T2",
    "text": "Exact reviewed resident rules text",
    "sha256": "SHA-256 of the UTF-8 text field"
  }
}
```

`move_resident.py plan <manifest>` is read-only and emits only provenance,
hashes and proposed configuration, not soul text. It makes no network call.

## Owner activation

1. Re-read the resident card for changed direction, pause/cancellation and owner.
   Review source plus the actual soul/T2 manifest. Confirm JEFF continuity is
   enabled. The installer refuses if it is not.
2. During the owner's next safe kdesk startup, supply
   `--resident-manifest <absolute manifest path>`. Use the pinned interpreter
   and the canonical reviewed source. Do not open a second writer on the live
   world or interrupt an active turn. The flag can be omitted on later starts.
3. Inspect Sable's House row, soul provenance, rules and private chat. Activate
   her through the existing world `set` word (`want=awake`). This does not start
   a model until she is addressed.
4. Alex sends a real message in **Talk with Sable**, reachable from her row in
   **Work**. Observe a real Sable reply and inspect her House log for task context.
   Do not simulate Alex's words with a builder session or mark the task done.
5. Only after that owner verification, prepare Pike separately. Ask the remaining
   residents whether they want to move as separate authorized coordination.

## Evidence and missing world words

Ran: `test_move_resident.py` uses retained private fixture worlds, real kernel
chat/address routing and scripted transport output. It covers private ownership,
idempotency, changed writing, conflicts, startup/session registration, addressed
wakes, own task projection, compaction and default JEFF behavior. No live model
trial, real Sable answer, desktop interaction or provider change was performed.

Rough spots for source review: the missing entry-service operation was
**provision a resident person/session at reviewed startup**; the missing House
fact was **addressed-only wake policy while retaining task context**.
Both use the existing kernel store and House module, with no parallel agent runner.
