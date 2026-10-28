# Reviewed resident moves: Sable, then Pike

Builder draft, 28 October 2026. The current card records JEFF's confirmation
that Sable answered and edited her soul. The mover now supports Pike as the
second, separate import. Nobody else is invited or woken by this code.

## What is ready

`move_resident.py` validates a review manifest and installs it through kdesk's
explicit `--resident-manifest` startup option. Normal startup changes nothing
about residents. Each resident receives a member account (not a steward), a distinct
person session, her soul, the resident T2 charter, a private chat with Alex,
and a House configuration with `next_steps=on`, `wake_policy=addressed`,
`want=asleep`. There is no fallback provider or old-card import.

The soul and charter belong to the resident's closed group, led by that resident and JEFF;
Alex retains steward access. Only those three can change the soul. Source text
is copied exactly, with source, source author, approval, review attribution and
SHA-256 recorded separately from the kernel's import authorship. Later resident
writing stays intact on reruns. A different source or hash refuses the import;
an ambiguous person, house-agent or session also refuses instead of adopting it.
Souls are signed by their resident; approved rules are signed by Alex. Rerunning
Sable's original reviewed manifest also corrects her charter's old `made_by`
attribution to Alex. It preserves her current soul and charter text, their
source provenance, and her session and House configuration. Unexpected charter
authorship refuses before changes.

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

No actual soul has been exported or imported by this worker. Obtain only the resident's
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

For Pike, use `"resident": "Pike"` and add a top-level `"sable_reply"` containing
the exact kernel `said` reference reviewed by the owner. The current card points
to Sable's settled reply in **Shop talk** (28 Oct, 19:54 UTC, `dk1171`), confirmed
by JEFF. The installer checks the referenced line is visible to Alex, nonempty,
and actually spoken by Sable, and that her House continuity is enabled with
addressed-only wakes. The review attribution still attests the owner's reading;
the code cannot judge what her reply means. The installed Pike House row retains
the reply reference as `move_after_reply`. A missing prerequisite refuses before
creating any person, session or belongings.

Pike's source named on the current card is old-desk soul `a578`. This is a source
pointer, not exported content or permission evidence. Inspect its exact revision,
authorship and access policy through the authorized archive interface, and
review only that soul before preparing Pike's manifest. Never substitute a new
soul or copy old task cards. Use the reviewed T2 everyone rules, authored by Alex.
This worker's existing Agora session reads kernel8810; no archive session or
credentials were changed to obtain the source.

## Owner activation

1. Re-read the resident card for changed direction, pause/cancellation and owner.
   Review source plus the actual soul/T2 manifest. Confirm JEFF continuity is
   enabled. The installer refuses if it is not.
2. During the owner's next safe kdesk startup, supply
   `--resident-manifest <absolute manifest path>`. Use the pinned interpreter
   and the canonical reviewed source. Do not open a second writer on the live
   world or interrupt an active turn. The flag can be omitted on later starts.
3. Inspect the resident's House row, soul provenance, rules and private chat. Activate
   her through the existing world `set` word (`want=awake`). This does not start
   a model until she is addressed.
4. Alex sends a real message in **Talk with Sable** or **Talk with Pike**, reachable
   from the resident's row in **Work**. Observe a real reply and inspect the House log for task context.
   Do not simulate Alex's words with a builder session or mark the task done.
5. Sable's owner confirmation is recorded on the live card. Install Pike separately
   using his reviewed manifest and that reply reference. JEFF checks Pike the
   same way. Invitations to other residents are not automated by this mover.

## Evidence and missing world words

Ran: `test_move_resident.py` uses retained private fixture worlds, real kernel
chat/address routing and scripted transport output. It covers private ownership,
idempotency, changed writing, conflicts, startup/session registration, addressed
wakes, own task projection, compaction and default JEFF behavior. No live model
trial, real resident answer, desktop interaction or provider change was performed
by this worker. The scripted lifecycle test covers both Sable and Pike. Additional
tests prove Pike cannot move before Sable's reply, another person's line cannot
satisfy that gate, and charter attribution repair retains current resident writing.

Rough spots for source review: the missing entry-service operation was
**provision a resident person/session at reviewed startup**; the missing House
fact was **addressed-only wake policy while retaining task context**.
Both use the existing kernel store and House module, with no parallel agent runner.
This follow-up extends the same startup operation to Pike with a reviewed
predecessor reply and repairs imported rules authorship. The startup help and
resident fixture tests were updated with it; House wake behavior is unchanged.
