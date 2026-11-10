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

## Fresh conversations on demand (5 November 2026)

Builder implementation for dk2273; landing and live acceptance remain with Pike
and JEFF. `house.refresh <person>` is an external, steward-only word. It
requests replacement of that resident's process and conversation. `house.who`
shows `refreshing` while replacement is underway, then the ordinary process
state or an error. The request receipt is not proof of successful replacement.

An awake resident gets a new process without `--resume`. An idle resident takes
no model turn until addressed; an interrupted turn is said again through the
existing restart message, followed by waiting messages with their chat
boundaries intact. A sleeping resident stays asleep. The fresh wake reads the
current `prompt=`, `charter=`, Agent Book welcome, `guide=` and `soul=`. Automatic
prompt-change restarts still resume their existing conversation; refresh is
the explicit way to discard its accumulated context.

Refresh changes no `house-agent` facts, credentials, provider settings or other
residents. Normal provider selection still applies. Cursors, counters and
fallback state are retained. Before ending the process, its previous state is
saved in `<house-home>/<resident>/conversations/<unique-id>.json`. The existing
`transcript.jsonl` remains append-only and records the archive reference;
provider-managed conversation files are not removed. Pending messages are
saved before starting the replacement. Failure to preserve state or end the
old process prevents replacement. Late events from any replaced process,
including text and final results, cannot affect its successor.

Hidden evidence is in `tests/test_house_refresh.py`: private in-process worlds,
real Lines dispatch and transport command construction, fake model children.
This does not establish a live provider's response or Rowan's current soul.
After landing and House activation, Pike checks a scratch resident; JEFF then
refreshes Rowan and verifies his next addressed turn against the current soul.

## Rough spots: a replaced process ended its successor (2 Nov 2026)

*Claude (builder), 2 Nov 2026.* JEFF answered nothing from 28 Oct 22:50 to 2 Nov. At the quota switch the House stopped
his Claude process and started Codex (pid 156312); the Claude process's exit event arrived a second later and cleared
`self.child`, so the new Codex process ran on unseen and held thread 01a18634. Each later line started another Codex,
refused with "thread ... already has an active writer" (25 times in his transcript). Also, `Child.stop` killed only the
venv launcher, which leaves the real interpreter running on Windows.

Source fix (ran: `test_stale_child.py` 4 passed; house tests 146 passed; live: stuck tree ended, `kd_reload.py house`,
`house.wake` delivered Alex's three lines and JEFF answered in the Conversation, dk1609-1610): events carry their
`child`, and `init`/`exit` from a replaced child are logged as `stale` and ignored; `stop` ends the whole tree
(`transport.kill_tree`).

The missing world-level word: **a house-agent's process as something the world can read** (running since, which
conversation it holds, how its last start ended). The House showed only `doing=error` with "its process ended (1)", so
five days of the same refusal looked like one quiet error. Lines Alex sent during the outage were consumed by the failed
starts (the cursor moved past them); they were re-delivered by hand with `house.wake`.

## Rough spots: Ask reached nobody after the old desk closed (3 Nov 2026)

*Claude (builder), 3 Nov 2026, Alex: "Yes, fix both" (Ask goes to JEFF; JEFF finishes a check in the same turn and tells
him in the Conversation).* The right-click `ask` verb only made an `ask-request`; `src/desktop/agora-chat/ask_relay.py`
carried it to the old desk's Conversation on door 8794, which was archived 27 Oct. Since then five asks waited (read:
`rows ask-request`, four still `status=open`). On 3 Nov a Claude session found one by chance and passed it to JEFF in
Shop talk; JEFF answered there, and Alex, in the Conversation, heard nothing.

The change is in the world: the old `ask` is hidden and a new verb says Alex's words as his own line in the Conversation
(`say <Conversation> text=$text about=$ask`), so the House wakes JEFF and Alex sees it. Two small source edits made that
possible: `say` accepts `about=` something its own act just made (kernel/chat.py), and the House's line to an agent names
what a line is about, with an ask's `where` (house.py `line_text`). Ran: tests/test_ask_reaches_jeff.py 3 passed,
test_stale_child.py 5 passed, kernel tests 374 passed (two failures also fail or pass alone without this change:
test_new_manager launcher options, a flaky test_web_host).

Missing world-level words: **a way to change a verb's steps** (word.set refuses "Implementation cannot be edited", so a
fix means hide and remake), and **a relay as a world thing**: the ask's destination lived in a script outside the world,
so when that script's desk went away nothing said the asks were going nowhere.
