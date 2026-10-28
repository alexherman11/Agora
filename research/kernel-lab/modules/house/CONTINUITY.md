# Task continuity port

Builder implementation, 27 October 2026. Source only; owner review and activation
remain required. Ports the behavior recorded in
`research/jeff-continuity/jeff-continuity-implementation.md` and the old
`notation/task_next_steps.py` (live checkpoint c70ace598), onto kernel facts,
visible readings, attributed records and the existing House wake path.

No archived cards, conversations or souls are imported. No timer, poller, model
call, credential, provider change or automatic completion is added.

## Reading and maintaining cards

`rows nextsteps:<person-id-or-name>` returns all visible responsible task rows.
Only its text/model packet is bounded: eight whole rows and fewer than 6,000
characters, with overflow count and the inspection command. Authored priority
sorts first; failures and activity do not promote a project.

Cards retain ordinary `goal`, `request_ref`, `next_action`, `acceptance`,
`parent_task`, `review_at`, owner/who/lead/asked_by, blocker, resolver and waiting
fields. Responsibility uses those explicit people; an unassigned card falls back
to its maker's person. JEFF does not silently acquire every card. A delegated card
should name its lead (for example `lead=JEFF`).

The five verbs retain old hyphen aliases and use the kernel's dotted names:

```text
task.next <task> next_action="Inspect the result" acceptance="The requested behavior works"
task.revise <task> goal="Corrected goal" acceptance="Corrected acceptance" request_ref=<request> next_action="Read the correction"
task.review <task> basis=<current-row-basis> next_action="Assess acceptance"
task.verify <task> basis=<current-row-basis> evidence=<visible-evidence-thing>
task.followup <task> review_at=2026-10-28T16:00:00-07:00
```

Old positional arguments work with an id or quoted task title. Followup retains
a timezone-bearing deadline; review-due appears at the next event or wake. It
does not arrange a timer.

Designated reviewer: lead, otherwise asker, otherwise owner/who, otherwise
maker's person. Review/verify inspect actual authorship, including an agent's
person. A worker's raw `set reviewed_basis=...` cannot borrow its lead's identity.
House's `build_phase=received` is receipt only; independent builder checks do not
author outcome verification. These verbs never close a task or parent.

The basis covers intent, authority, direct child results, received result version
and referenced result-evidence revisions. Cosmetic changes and next-action edits
do not invalidate review. Material edits invalidate claims; undo restores the
previous material basis. Verification needs acceptance and a current visible
world evidence subject authored with the token in the same record. Evidence-only
swaps, subsequent evidence edits and undone attestations do not count.

As in the original, verification is an attributed owner judgment, not a host
evaluation of arbitrary prose acceptance. New kernel words implement the
projection and guards; dictionary names, help and access policy remain world data.
The new world has no native promise substrate to port; no legacy promises are
imported or invented here.

## Delivery and activation

After normal source review/landing, load the kernel word implementation and
House/transport source. Both running kernel and resident process must use the
new source for immediate compaction hooks. Do not stop an active turn for this
worker's result; the owner coordinates the existing safe activation lifecycle.

The owner enables `next_steps=on` on JEFF's existing house-agent thing. Its
current value is read again after compaction. `next_steps=off` removes automatic
context without removing card data. No provider, credential or grant change is
needed for the existing House `rows`, `look`, `hear:make`, `hear:set`,
`hear:undo`, `hear:task.*` grants.

On each ordinary wake, fresh entry, resumed entry or provider handoff, House
reads current rows through the resident's existing session. Failed sends retain
the original instruction; retry rereads current cards. Relevant happenings
compare the projection and queue one changed-context wake. Invisible cards do
not change it. There is no polling. Existing sleep and turn-queue gates remain.
`forget` is not among House's existing hearing grants; a forgotten subject is
removed at the next supported event or ordinary wake.

Claude's existing SessionStart hook reads the charter and tasks during
compaction. Codex's existing compaction callback injects the same context into
the same thread as a developer item. House also retains a continuation wake
after the current turn, covering both transports without an unsolicited chat
message. A pickup outside chat is inspectable through existing
`house.activity JEFF` and `house.log JEFF`.

## Evidence

`tests/test_next_steps.py` uses private in-process kernel worlds and scripted
transport doubles: fresh wake, task-only event, inspectable activity,
compaction, same-thread Codex injection, off switch, deduplication, failed
send/correction, privacy, row/character bounds, priority, review attribution,
stale basis, evidence swap/edit, undo, and separate parent acceptance.

The activity acknowledgment is scripted evidence, not a claim that the live
JEFF model has picked up a card. After activation, observe a normal task-only
event and inspect JEFF's activity before calling that acceptance verified.
No live model trial was run by this worker.
